from app.api_requests import wait_on_run
from app.api_requests import thread
from app.api_requests import client
from app.api_requests import assistant_id
from app.api_requests import get_latest_assistant_response

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
