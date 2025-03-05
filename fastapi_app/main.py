from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import time
import re
from openai import AzureOpenAI

# Initialize FastAPI
app = FastAPI()

# Fetch Environment Variables
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
assistant_id = os.getenv("ASSISTANT_ID")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

# Pydantic Models (No `assistant_id` in request schema)
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    messages: List[Message]

class ChatResponse(BaseModel):
    thread_id: str
    message_id: str
    role: str
    content: Optional[str]

# Function to Wait for Assistant Response
def wait_for_response(thread_id, run_id):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status not in ["queued", "in_progress"]:
            break
        time.sleep(0.5)

    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
    for msg in messages.data:
        if msg.role == "assistant" and hasattr(msg, 'content') and msg.content:
            response_text = (
                msg.content[0].text.value if isinstance(msg.content, list) else msg.content
            )
            cleaned_response = re.sub(r"【\d+:\d+†source】", "", response_text)
            return cleaned_response, msg.id
    return None, None

# Chat API Endpoint (Assistant ID Removed from Request)
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        if not assistant_id:
            raise HTTPException(status_code=500, detail="ASSISTANT_ID is not set.")

        # Create a new thread if not provided
        thread_id = request.thread_id or client.beta.threads.create().id

        # Process user messages
        for message in request.messages:
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role=message.role,
                content=message.content,
            )

        # Run the assistant (Assistant ID is set internally)
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id  # Passed internally, never in request
        )

        assistant_response, message_id = wait_for_response(thread_id, run.id)

        if assistant_response and message_id:
            return ChatResponse(
                thread_id=thread_id,
                message_id=message_id,
                role="assistant",
                content=assistant_response
            )
        else:
            raise HTTPException(status_code=404, detail="No response from assistant.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
