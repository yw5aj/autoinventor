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
import openai
import requests
import graphviz
import json
import uuid

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Client(api_key=ANTHROPIC_API_KEY)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize BigQuery client
bigquery_client = bigquery.Client()


# Create a user interface to take the user prompt
def user_interface():
    print("Welcome to the Auto Inventor!")
    print("Please enter the field of invention or the problem you want to solve:")
    user_prompt = input()
    return user_prompt


# Pass the user prompt to the researcher module
def researcher_module(user_prompt, max_attempts=5):
    print("Researching the user prompt...")
    print("User prompt:", user_prompt)

    attempts = 0
    patents = pd.DataFrame()

    while len(patents) < 3 and attempts < max_attempts:
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
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"Generate a list of 5 keywords related to the following invention or problem: {user_prompt}." 
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

    response = anthropic_client.messages.create(
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

    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    invention_document = response.content[0].text.strip()

    # Strip the ```markdown and ``` at the beginning and end of the invention document
    invention_document = invention_document.replace("```markdown", "").replace("```", "")

    print("Generated invention description document:")
    print(invention_document)
    
    return invention_document


def diagram_module(invention_document, num_images=2, num_flowcharts=2):
    print("Generating diagrams for the invention document...")

    # Generate the descriptions of num_images number of images for the invention document
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": f"Generate the prompts of {num_images} number of diagrams for the following invention document: {invention_document}. I want to include these diagrams in the final patent, so make them very minimalistic and simple. Ideally only lines and shapes. Format your response with just the descriptions of the diagrams, separated by [separator], each string representing the description of a diagram."
            }
        ]
    )

    # The response content is a list of strings, each string representing the description of a diagram
    image_descriptions = response.content[0].text.strip().split("[separator]")

    # Clean the empty strings from the list
    image_descriptions = [description.strip() for description in image_descriptions if description.strip()]

    # Generate the images for the invention document using OpenAI API
    # Store the image paths and descriptions in a list of dictionaries
    images = []
    for image_id, image_description in enumerate(image_descriptions):
        print(f"Generating image: {image_description}")
        # Use OpenAI API to generate the image
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=image_description,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url

        # Create the images folder if it doesn't exist
        os.makedirs("images", exist_ok=True)

        # Download the image and save it to the images folder named with image_{number}.png
        image_response = requests.get(image_url)
        unique_id = uuid.uuid4().hex[:8]  # Generate a short unique identifier
        image_path = f"images/image_{unique_id}.png"
        with open(image_path, "wb") as image_file:
            image_file.write(image_response.content)
        print(f"Saved image to {image_path}")

        # Store the image path and description in the list of dictionaries
        images.append({"id": unique_id, "path": image_path, "description": image_description})


    # Now generate flowcharts alongside with the images
    # Generate the descriptions of num_flowcharts number of flowcharts for the invention document
    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": f"Generate the prompts of {num_flowcharts} number of flowcharts for the following invention document: {invention_document}. I want to include these flowcharts in the final patent, with graphviz. Format your response with just the descriptions of the flowcharts, separated by [separator], each string representing the description of a flowchart."
            }
        ]
    )

    # The response content is a list of strings, each string representing the description of a flowchart
    flowchart_descriptions = response.content[0].text.strip().split("[separator]")

    # Clean the empty strings from the list
    flowchart_descriptions = [description.strip() for description in flowchart_descriptions if description.strip()]

    flowcharts = []
    # Generate the flowcharts for the invention document using Graphviz
    for flowchart_id, flowchart_description in enumerate(flowchart_descriptions):
        print(f"Generating flowchart: {flowchart_description}")
        # Use Graphviz to generate the flowchart
        prompt = f"""
        Based on the following flowchart description, return a JSON object with a 'title' and a list of 'steps'.
        Each step should be a concise phrase.

        Flowchart description:
        {flowchart_description}

        Format:
        {{
            "title": "Flowchart Title",
            "steps": [
                "Step 1",
                "Step 2",
                "Step 3",
                ...
            ]
        }}
        """

        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Parse the JSON response
        flowchart_data = json.loads(response.content[0].text)

        # Create and save the flowchart in the flowcharts folder
        os.makedirs("flowcharts", exist_ok=True)

        flowchart = create_flowchart(flowchart_data['title'], flowchart_data['steps'])
        unique_id = uuid.uuid4().hex[:8]  # Generate a short unique identifier
        flowchart_path = f"flowcharts/flowchart_{unique_id}"
        flowchart.render(flowchart_path, format='png', cleanup=True)
        print(f"Saved flowchart to {flowchart_path}.png")

        # Store the flowchart path and description in the list of dictionaries
        flowcharts.append({"id": unique_id, "path": f"{flowchart_path}.png", "description": flowchart_description})

    return images, flowcharts


def create_flowchart(title, steps):
    dot = graphviz.Digraph(comment=title)
    dot.attr(rankdir='TB', size='8,8')
    
    for i, step in enumerate(steps):
        dot.node(f'step_{i}', step)
        if i > 0:
            dot.edge(f'step_{i-1}', f'step_{i}')
    
    return dot


# Use the input from writer module to create a patent for the best invention
def patentor_module(invention_document, images, flowcharts):
    print("Creating a patent document...")

    # Prepare image and flowchart descriptions
    image_descriptions = "\n".join([f"Figure {i+1}: {img['description']}" for i, img in enumerate(images)])
    flowchart_descriptions = "\n".join([f"Flowchart {i+1}: {fc['description']}" for i, fc in enumerate(flowcharts)])

    prompt = f"""
        Convert the following invention description into a formal patent document. Include the following sections:

        1. Title of Invention
        2. Field of the Invention
        3. Background of the Invention
        4. Summary of the Invention
        5. Brief Description of the Drawings
        6. Detailed Description of the Invention
        7. Claims
        8. Abstract

        Ensure the document follows standard patent formatting and language. Be thorough and precise in your descriptions and claims.

        Invention Document:
        {invention_document}

        Images:
        {image_descriptions}

        Flowcharts:
        {flowchart_descriptions}

        In the "Brief Description of the Drawings" section, include descriptions of all images and flowcharts.
        In the "Detailed Description of the Invention" section, reference the figures and flowcharts where appropriate.

        Please format your response in Markdown, using appropriate headers for each section.
        """

    response = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    patent_document = response.content[0].text.strip()

    # Strip the ```markdown and ``` at the beginning and end of the patent document
    patent_document = patent_document.replace("```markdown", "").replace("```", "")
     
    print("Generated patent document:")
    print(patent_document)
    return patent_document


def create_final_report(user_prompt, relevant_patents, invention_ideas, invention_document, images, flowcharts, patent_document):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"auto_inventor_report_{timestamp}.md"
    
    # Convert relevant_patents to a text formatted patent summary with title, abstract and publication number
    patents_md = relevant_patents.apply(lambda row: f"""
### {row['publication_number']}: {row['title']}

#### Abstract
{row['abstract']}
        """, axis=1).tolist()
    patents_md = "\n\n".join(patents_md)
    
    # Create markdown for images
    images_md = "\n\n".join([f"![Image {img['id']}]({img['path']})\n\n{img['description']}" for img in images])
    
    # Create markdown for flowcharts
    flowcharts_md = "\n\n".join([f"![Flowchart {fc['id']}]({fc['path']})\n\n{fc['description']}" for fc in flowcharts])
    
    report_content = f"""
# Auto Inventor Report

## 1. User Prompt
{user_prompt}

## 2. Relevant Patents
{patents_md}

## 3. Invention Ideas
{invention_ideas}

## 4. Invention Document
{invention_document}

## 5. Images
{images_md}

## 6. Flowcharts
{flowcharts_md}

## 7. Patent Document
{patent_document}
        """

    with open(filename, "w", encoding="utf-8") as file:
        file.write(report_content)
    
    print(f"Final report saved as {filename}")

    return filename


if __name__ == "__main__":
    user_prompt = user_interface()
    # For testing purposes, we will use the test prompt
    # user_prompt = "use 3D printing to create a more efficient and affordable prosthetic leg"
    relevant_patents = researcher_module(user_prompt)
    invention_ideas = inventor_module(user_prompt, relevant_patents)
    invention_document = writer_module(invention_ideas)
    images, flowcharts = diagram_module(invention_document)
    patent_document = patentor_module(invention_document, images, flowcharts)
    final_report_filename = create_final_report(user_prompt, relevant_patents, invention_ideas, invention_document, images, flowcharts, patent_document)
    print(f"Final report saved as: {final_report_filename}")