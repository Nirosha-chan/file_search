from app.api_requests import client 
from app.thread import thread
import re

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