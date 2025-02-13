from fastapi import FastAPI, HTTPException
from openai import AzureOpenAI
from fastapi_app.routers import chat
from pydantic import BaseModel
import time
import re

# Initialize FastAPI app
app = FastAPI()

# Azure OpenAI Client Configuration
endpoint = "https://oai-assistantapi-poc.openai.azure.com/"
api_key = "fcaa6ab31d5048c38e309e029edc2721"
api_version = "2024-08-01-preview"
assistant_id = "asst_WrR5VTYyJH7IEUOJeioxOtzO"

# Initialize AzureOpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

# Store threads in memory (for demonstration purposes)
thread_store = {}

class UserMessage(BaseModel):
    thread_id: str
    message: str

def wait_on_run(run, thread_id):
    """Wait for assistant's response"""
    while run.status in ["queued", "in_progress"]:
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
    return run

def get_latest_assistant_response(thread_id):
    """Retrieve and clean the assistant response"""
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
    for msg in messages.data:
        if msg.role == "assistant" and hasattr(msg, 'content') and msg.content:
            if isinstance(msg.content, list):
                response_text = msg.content[0].text.value
            else:
                response_text = msg.content
            cleaned_response = re.sub(r"【\d+:\d+†source】", "", response_text)
            return cleaned_response
    return None

@app.post("/start-thread")
def start_thread():
    """Start a new conversation thread"""
    thread = client.beta.threads.create()
    thread_store[thread.id] = thread
    return {"thread_id": thread.id, "message": "Thread started"}

@app.post("/send-message")
def send_message(user_msg: UserMessage):
    """Handle user message and get assistant response"""
    thread_id = user_msg.thread_id
    user_input = user_msg.message

    if thread_id not in thread_store:
        raise HTTPException(status_code=400, detail="Invalid thread ID")

    # Create a new message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input,
    )

    # Run assistant
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    run = wait_on_run(run, thread_id)

    # Retrieve response
    assistant_response = get_latest_assistant_response(thread_id)
    if assistant_response is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve assistant response")
    return {"assistant_response": assistant_response}
