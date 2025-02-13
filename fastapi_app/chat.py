from fastapi import APIRouter

router = APIRouter()

@router.post("/send-message")
async def send_message():
    return {"message": "Hello from chat router"}
