
from fastapi import APIRouter

router = APIRouter()

# Lazy import inside a function
def import_main():
    from app.chat import get_latest_assistant_response
    return get_latest_assistant_response
