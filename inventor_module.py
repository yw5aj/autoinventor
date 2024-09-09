# Use the input from researcher module to generate a list of possible inventions
import os
from autogen import ConversableAgent
from datetime import datetime

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
    initial_invention_ideas = response.content[0].text.strip()

    conversation_start = f"""
Hi I am thinking of filing a patent related to {user_prompt}

Can you provide some feedbacks on how to improve on my potential invention ideas?
{initial_invention_ideas}
        """

    inventor_reviewer_agent = ConversableAgent(
        "Inventor Reviewer",
        system_message="You are an expert inventor reviewer and you will provide constructive and critical feedback for the inventor's ideas. Only focus on what edits or changes should be improved for each idea. Be sharp",
        llm_config={"config_list": [{"model": "claude-3-sonnet-20240229", "temperature": 0.7, "api_key": os.environ.get("ANTHROPIC_API_KEY"), "api_type":"anthropic"}]},
        human_input_mode="ALWAYS",  
    )

    inventor_agent = ConversableAgent(
        "Inventor",
        system_message="""
        You are an inventor and your end goal is to generate a list of plausible invention ideas, improve your answer by incorporating the feedback, always return your answer with the following format
        1. Invention Title 1
        Brief description of the invention

        2. Invention Title 2
        Brief description of the invention

        3. Invention Title 3
        Brief description of the invention""",
        llm_config={"config_list": [{"model": "claude-3-sonnet-20240229", "temperature": 0.7, "api_key": os.environ.get("ANTHROPIC_API_KEY"), "api_type":"anthropic"}]},
        human_input_mode="NEVER",  # Never ask for human input.
    )

    carryover = f"""
Here are some relevant patents related to {user_prompt}
Relevant Patents:
{patent_input}
    """
    
    chat_result = inventor_agent.initiate_chat(
        inventor_reviewer_agent,
        message=conversation_start,
        carryover=carryover,
        max_turns=3,
    )

    # TODO: modify the code to have the inventor to reply to the last message, and include that in the chat history
    # Extract the invention ideas from the last message
    invention_ideas = chat_result.chat_history[-2]['content']
    
    print("Generated invention ideas:")
    print(invention_ideas)
    
    # Save chat history to a file
    chat_history_filename = save_chat_history(chat_result.chat_history[:-1])
    
    return invention_ideas, chat_result.chat_history, chat_history_filename

def format_chat_history_as_markdown(chat_history):
    markdown_output = "# Invention Ideas Generation Chat History\n\n"
    for i, message in enumerate(chat_history):
        # Determine the agent name based on the message index
        if i % 2 == 0:
            name = "Inventor"
        else:
            name = "Inventor Reviewer"
        
        content = message['content']
        markdown_output += f"## {name}\n\n{content}\n\n"
    return markdown_output

def save_chat_history(chat_history):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chat_history_filename = f"chat_history_{timestamp}.md"
    
    chat_history_md = format_chat_history_as_markdown(chat_history)
    with open(chat_history_filename, "w", encoding="utf-8") as file:
        file.write(chat_history_md)
    
    print(f"Chat history saved as: {chat_history_filename}")
    return chat_history_filename
