from app.api_requests import client

# Use the existing Product Information Assistant by its ID
assistant_id = "asst_WrR5VTYyJH7IEUOJeioxOtzO"

# Create a new thread for the conversation
thread = client.beta.threads.create()
print("Thread started. Type 'exit' to quit.")
