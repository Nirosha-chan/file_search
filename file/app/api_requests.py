from openai import AzureOpenAI
import time
import re

# Replace with your Azure OpenAI details
endpoint = "https://oai-assistantapi-poc.openai.azure.com/"  
api_key = "fcaa6ab31d5048c38e309e029edc2721"

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,        
    api_key=api_key,                    
    api_version="2024-05-01-preview"  
)

# Use the existing Product Information Assistant by its ID
assistant_id = "asst_WrR5VTYyJH7IEUOJeioxOtzO"

# Create a new thread for the conversation
thread = client.beta.threads.create()
print("Thread started. Type 'exit' to quit.")

# Helper function to wait for the assistant's response
def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
    return run

# Function to get the latest assistant response
def get_latest_assistant_response(thread):
    """Fetches and cleans the latest assistant response from the conversation thread."""
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc")  # Get the latest messages first
    for msg in messages.data:
        if msg.role == "assistant":
            if msg.content and isinstance(msg.content, list):  # Ensure content exists
                response_text = msg.content[0].text.value
                # Remove source reference patterns like  
                cleaned_response = re.sub(r"【\d+:\d+†source】", "", response_text)
                return cleaned_response
    return None

# Function to handle user conversation
def handle_user_conversation():
    """Manages the conversation between the user and the assistant."""
    while True:
        # Read user input
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting conversation.")
            break

        # Create a new user message in the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
        )

        # Run the assistant for the new message
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )

        # Wait for the run to complete
        run = wait_on_run(run, thread)

        # Retrieve the assistant's response
        assistant_response = get_latest_assistant_response(thread)
        if assistant_response:
            print(f"\nAssistant: {assistant_response}\n")

# Start the conversation handling
handle_user_conversation()
