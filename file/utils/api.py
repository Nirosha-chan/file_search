
from fastapi import APIRouter

router = APIRouter()

# Lazy import inside a function
def import_main():
    from fastapi_app.main import get_latest_assistant_response
    return get_latest_assistant_response
