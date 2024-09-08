# Create the main file for auto inventor project, which leverages LLMs to generate inventions
# The main modules and steps are as follows:
# 0. Interface module will take user inputs such as the field of invention or the problem they want to solve
# 1. Researcher module will search for relevant patents and inventions
# 2. Inventor module will analyze the research and create a list of possible inventions, and choose the best one
# 3. Writer module will write a report on the best invention, with detailed descriptions and diagrams
# 4. Patentor module will create a patent for the invention


import os
import anthropic
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

# Initialize BigQuery client
bigquery_client = bigquery.Client()


# Create a user interface to take the user prompt
def user_interface():
    print("Welcome to the Auto Inventor!")
    print("Please enter the field of invention or the problem you want to solve:")
    user_prompt = input()
    return user_prompt


# Pass the user prompt to the researcher module
def researcher_module(user_prompt, max_attempts=3):
    print("Researching the user prompt...")
    print("User prompt:", user_prompt)

    attempts = 0
    patents = pd.DataFrame()

    while len(patents) == 0 and attempts < max_attempts:
        # Generate keywords from the user prompt
        keywords = generate_keywords(user_prompt)
        print("Generated keywords:", ", ".join(keywords))

        # Search for relevant patents and inventions
        patents = search_patents(keywords)

        if len(patents) == 0:
            attempts += 1
            print(f"No patents found. Attempt {attempts} of {max_attempts}.")
            if attempts < max_attempts:
                print("Retrying with different keywords...")
            else:
                print("Maximum attempts reached. Unable to find relevant patents.")
        else:
            print(f"Found {len(patents)} relevant patents")

    return patents


def search_patents(keywords):
    print("Searching for relevant patents and inventions...")
    print("Keywords:", ", ".join(keywords))

    # Construct the query
    query = f"""
    SELECT
      publication_number,
      (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1) AS title,
      (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1) AS abstract
    FROM
      `patents-public-data.patents.publications`
    WHERE
      REGEXP_CONTAINS(LOWER(CONCAT(
        IFNULL((SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1), ''), ' ',
        IFNULL((SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1), '')
      )), r'(?i){"|".join(keywords)}')
    LIMIT 10
    """

    # Run the query
    query_job = bigquery_client.query(query)
    results = query_job.result()

    # Convert results to a pandas DataFrame
    df = results.to_dataframe()
    
    return df



def generate_keywords(user_prompt):
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"Generate a list of 5-10 keywords related to the following invention or problem: {user_prompt}." 
                             "I am going to use these keywords to search for relevant patents and inventions."
                             "Please format the keywords as a comma-separated list."
            }
        ]
    )
    # Assuming the response content is a comma-separated string of keywords
    keywords = response.content[0].text.strip().split(", ")
    return keywords


# Use the input from researcher module to generate a list of possible inventions
def inventor_module(user_prompt, relevant_patents):
    print("Generating a list of possible inventions...")
    
    # Prepare the input for the AI
    patent_summaries = relevant_patents.apply(lambda row: f"Title: {row['title']}\nAbstract: {row['abstract']}", axis=1).tolist()
    patent_input = "\n\n".join(patent_summaries)
    
    prompt = f"""
        Given the following user prompt and summaries of relevant patents, generate three new and innovative ideas that could potentially be patented to address the problem. Each idea should be novel and not directly copy existing patents.

        User Prompt: {user_prompt}

        Relevant Patents:
        {patent_input}

        Please provide three unique invention ideas, each with a title and a brief description. Format your response as follows:

        1. Invention Title 1
        Brief description of the invention

        2. Invention Title 2
        Brief description of the invention

        3. Invention Title 3
        Brief description of the invention

        Please format your response in Markdown, using appropriate headers for each section.
        """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    invention_ideas = response.content[0].text.strip()
    print("Generated invention ideas:")
    print(invention_ideas)
    
    return invention_ideas

# Use the input from inventor module to write a report on the best invention
def writer_module(invention_ideas):
    print("Writing a detailed invention description document...")

    prompt = f"""
        Based on the following invention ideas, please draft a comprehensive invention description document for the most promising idea. Include the following key components:

        1. Invention Title
        2. Detailed Invention Description
        3. Key Points and Advantages
        4. Abstract

        You may add more sections if you see fit. The document should be thorough and well-structured, suitable for patent filing purposes.

        Invention Ideas:
        {invention_ideas}

        Please format your response in Markdown, using appropriate headers for each section.
        """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    invention_document = response.content[0].text.strip()
    print("Generated invention description document:")
    print(invention_document)
    
    return invention_document

# Use the input from writer module to create a patent for the best invention
def patentor_module(invention_document):
    print("Creating a patent document...")

    prompt = f"""
        Convert the following invention description into a formal patent document. Include the following sections:

        1. Title of Invention
        2. Field of the Invention
        3. Background of the Invention
        4. Summary of the Invention
        5. Brief Description of the Drawings (if applicable)
        6. Detailed Description of the Invention
        7. Claims
        8. Abstract

        Ensure the document follows standard patent formatting and language. Be thorough and precise in your descriptions and claims.

        Invention Document:
        {invention_document}

        Please format your response in Markdown, using appropriate headers for each section.
        """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    patent_document = response.content[0].text.strip()

     
    print("Generated patent document:")
    print(patent_document)
    return patent_document


def create_final_report(user_prompt, relevant_patents, invention_ideas, invention_document, patent_document):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"auto_inventor_report_{timestamp}.md"
    
    # Convert relevant patents to a more Markdown-friendly format
    patents_md = "| publication_number | title | abstract |\n|:-------------------|:------|:---------|\n"
    for _, row in relevant_patents.iterrows():
        patents_md += f"| {row['publication_number']} | {row['title']} | {row['abstract']} |\n"
    
    report_content = f"""
        # Auto Inventor Report

        ## 1. User Prompt
        ```markdown
        {user_prompt}
        ```

        ## 2. Relevant Patents
        {patents_md}

        ## 3. Invention Ideas
        {invention_ideas}

        ## 4. Invention Document
        {invention_document}

        ## 5. Patent Document
        {patent_document}
        """

    with open(filename, "w", encoding="utf-8") as file:
        file.write(report_content)
    
    print(f"Final report saved as {filename}")

    return filename


if __name__ == "__main__":
    # user_prompt = user_interface()
    # For testing purposes, we will use the test prompt
    user_prompt = "use 3D printing to create a more efficient and affordable prosthetic leg"
    relevant_patents = researcher_module(user_prompt)
    invention_ideas = inventor_module(user_prompt, relevant_patents)
    invention_document = writer_module(invention_ideas)
    patent_document = patentor_module(invention_document)
    final_report_filename = create_final_report(user_prompt, relevant_patents, invention_ideas, invention_document, patent_document)
    print(f"Final report saved as: {final_report_filename}")