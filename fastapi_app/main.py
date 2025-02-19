from fastapi import FastAPI, HTTPException, APIRouter
from openai import AzureOpenAI
from pydantic import BaseModel
from typing import Optional, List
import time
import re

# Initialize FastAPI app
app = FastAPI()

# Azure OpenAI Client Configuration
endpoint = "AZURE_ENDPOINT_URL"
api_key = "AZURE_API_KEY"
api_version = "2024-08-01-preview"
assistant_id = "asst_WrR5VTYyJH7IEUOJeioxOtzO"

# Initialize AzureOpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

router = APIRouter()

# Define the Pydantic models
class Message(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    thread_id: str
    message_id: str
    role: str
    assist_id: Optional[str]
    content: Optional[str]

class UserMessage(BaseModel):
    message: str

def wait_for_response(thread_id, run_id):
    """Wait for assistant's response and retrieve it in a single API call"""
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
            cleaned_response = re.sub(r"【\\d+:\\d+†source】", "", response_text)
            return cleaned_response
    return None

@app.post("/send-message")
def send_message(user_msg: UserMessage):
    """Start a thread if it doesn't exist and handle user message with assistant response in a single API call"""
    # Create a new thread
    thread = client.beta.threads.create()
    thread_id = thread.id

    # Send user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_msg.message,
    )

    # Run assistant and retrieve response
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    assistant_response = wait_for_response(thread_id, run.id)

    if assistant_response is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve assistant response")

    return {"thread_id": thread_id, "assistant_response": assistant_response}

app.include_router(router)
