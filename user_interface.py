import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

def user_interface():
    print("Welcome to the Auto Inventor!")
    print("Please enter the field of invention, the problem you want to solve, or the path to a meeting recording file:")
    user_input = input().strip()

    if os.path.isfile(user_input):
        # It's a file path, so transcribe and summarize
        return process_audio_file(user_input)
    else:
        # It's a direct prompt
        return user_input

def process_audio_file(file_path):
    # Transcribe the audio file
    transcript = transcribe_audio(file_path)
    
    # Summarize the transcript
    summary = summarize_transcript(transcript)
    
    return summary

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcript.text

def summarize_transcript(transcript):
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant tasked with summarizing meeting transcripts to identify the main problem or invention idea discussed."},
            {"role": "user", "content": f"Please summarize the following meeting transcript, focusing on the main problem or invention idea discussed:\n\n{transcript}"}
        ]
    )
    return response.choices[0].message.content