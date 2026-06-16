from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

@router.get("/")
def status_chat():
    return {"message": "Rota do Chatbot em construção"}