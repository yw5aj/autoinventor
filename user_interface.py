import os
import openai
from dotenv import load_dotenv
import markdown
import pymupdf4llm
from bs4 import BeautifulSoup
import docx2txt
import time

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def user_interface():
    print("Welcome to the Auto Inventor!")
    print("Please enter the field of invention, the problem you want to solve, or the path to a folder containing relevant files:")
    user_input = input().strip()

    if os.path.isdir(user_input):
        # It's a folder path, so process all files
        return process_folder(user_input)
    else:
        # It's a direct prompt
        return user_input

def process_folder(folder_path):
    summaries = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            file_summary = process_file(file_path)
            if file_summary:
                print(f"\nSummary of {filename}:")
                print(file_summary)
                summaries.append(f"Summary of {filename}:\n{file_summary}")
    
    # Combine all summaries
    combined_summary = "\n\n".join(summaries)
    
    # Generate a final summary
    final_summary = summarize_text(combined_summary)
    print("\nFinal summary of all files:")
    print(final_summary)
    return final_summary

def process_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension in ['.mp3', '.wav', '.m4a']:
        return process_audio_file(file_path)
    elif file_extension == '.pdf':
        return process_pdf_file(file_path)
    elif file_extension in ['.txt', '.md']:
        return process_text_file(file_path)
    elif file_extension in ['.docx', '.doc']:
        return process_word_file(file_path)
    elif file_extension in ['.html', '.htm']:
        return process_html_file(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return None

def process_audio_file(file_path):
    transcript = transcribe_audio(file_path)
    return summarize_text(transcript)

def process_pdf_file(file_path):
    md_text = pymupdf4llm.to_markdown(file_path)
    return summarize_text(md_text)

def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
        if file_path.endswith('.md'):
            text = markdown.markdown(text)
    return summarize_text(text)

def process_word_file(file_path):
    text = docx2txt.process(file_path)
    return summarize_text(text)

def process_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        # Extract the main content (you might need to adjust this based on the HTML structure)
        main_content = soup.find('body')
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
    return summarize_text(text)

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

def chunk_text(text, chunk_size=3000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    for word in words:
        if current_size + len(word) > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def summarize_text(text, model="gpt-3.5-turbo"):
    chunks = chunk_text(text)
    summaries = []
    for chunk in chunks:
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant tasked with summarizing text to identify the main problems or invention ideas discussed."},
                    {"role": "user", "content": f"Please summarize the following text, focusing on the main problems or invention ideas discussed:\n\n{chunk}"}
                ]
            )
            summaries.append(response.choices[0].message.content)
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting for 60 seconds before retrying.")
            time.sleep(60)
            return summarize_text(text, model)  # Retry after waiting
    
    combined_summary = " ".join(summaries)
    
    if len(combined_summary) > 3000 and model != "gpt-4":
        return summarize_text(combined_summary, "gpt-4")
    return combined_summary

if __name__ == "__main__":
    user_prompt = user_interface()
    print(user_prompt)
