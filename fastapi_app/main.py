from fastapi import FastAPI, HTTPException
from openai import AzureOpenAI
from pydantic import BaseModel
from typing import Optional, List
import time
import re

# Initialize FastAPI app
app = FastAPI()

# Azure OpenAI Client Configuration
endpoint = "AZURE_ENDPOINT_URL"  # Replace with your endpoint
api_key = "AZURE_API_KEY"                # Replace with your API key
api_version = "2024-08-01-preview"
assistant_id = "asst_WrR5VTYyJH7IEUOJeioxOtzO"

# Initialize AzureOpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

# Define Pydantic models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    assist_id: str
    messages: List[Message]

class ChatResponse(BaseModel):
    thread_id: str
    content: Optional[str]

# Helper function to wait for the assistant's response
def wait_for_response(thread_id, run_id):
    """Wait for the assistant's response and retrieve only the content."""
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status not in ["queued", "in_progress"]:
            break
        time.sleep(0.5)

    # Retrieve the latest assistant message
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
    for msg in messages.data:
        if msg.role == "assistant" and hasattr(msg, 'content') and msg.content:
            response_text = (
                msg.content[0].text.value if isinstance(msg.content, list) else msg.content
            )
            # Clean up any unwanted patterns from the response
            cleaned_response = re.sub(r"【\\d+:\\d+†source】", "", response_text)
            return cleaned_response
    return None

# Single endpoint to handle chat and manage thread creation
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Handles chat requests by:
    - Creating a thread if thread_id isn't provided.
    - Sending user messages.
    - Returning only the thread_id and content in the response.
    """
    try:
        # Create a new thread if one isn't provided
        if not request.thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
        else:
            thread_id = request.thread_id

        # Process each user message
        for message in request.messages:
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role=message.role,
                content=message.content,
            )
            # Run the assistant for the new message
            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=request.assist_id)
            wait_for_response(thread_id, run.id)  # Wait for assistant's run to complete

        # Retrieve only the assistant's content after the run completes
        assistant_response = wait_for_response(thread_id, run.id)

        if assistant_response:
            return ChatResponse(
                thread_id=thread_id,
                content=assistant_response
            )
        else:
            raise HTTPException(status_code=404, detail="No response from assistant.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
