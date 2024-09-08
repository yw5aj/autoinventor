# Use the input from researcher module to generate a list of possible inventions
import os

def inventor_module(client, user_prompt, relevant_patents):
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


    cathy = ConversableAgent(
        "Inventor Reviewer",
        system_message="You are an expert inventor reviewer and you will provide constructive feedback for the inventor proposal",
        llm_config={"config_list": [{"model": "claude-3-sonnet-20240229", "temperature": 0.7, "api_key": os.environ.get("ANTHROPIC_API_KEY"), "api_type":"anthropic"}]},
        human_input_mode="NEVER",  # Never ask for human input.
    )

    joe = ConversableAgent(
        "Inventor",
        system_message="Your name is Joe and you are a part of a duo of comedians.",
        llm_config={"config_list": [{"model": "claude-3-sonnet-20240229", "temperature": 0.7, "api_key": os.environ.get("ANTHROPIC_API_KEY"), "api_type":"anthropic"}]},
        human_input_mode="NEVER",  # Never ask for human input.
    )
    
    invention_ideas = response.content[0].text.strip()
    print("Generated invention ideas:")
    print(invention_ideas)
    
    return invention_ideas
