import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, ChatMessage
from app.schemas import ChatRequest, ChatResponse
from app.auth import get_current_user
from app.services.gemini_service import generate_chat_response

router = APIRouter(prefix="/chat", tags=["Multilingual AI Chat"])

@router.post("/send", response_model=ChatResponse)
def send_chat_message(
    chat_req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends message to multilingual JalDoot AI assistant (Hindi, English, Gujarati).
    Saves message and assistant response to database with explainability factors.
    """
    if not chat_req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    lat = chat_req.latitude or 21.63
    lon = chat_req.longitude or 69.60

    # 1. Generate AI Response
    ai_result = generate_chat_response(
        message=chat_req.message,
        requested_lang=chat_req.language or "auto",
        latitude=lat,
        longitude=lon
    )

    # 2. Save user message to database
    user_msg_db = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=chat_req.message,
        language=ai_result["detected_language"]
    )
    db.add(user_msg_db)

    # 3. Save assistant message with explainable metadata
    bot_msg_db = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=ai_result["reply"],
        language=ai_result["detected_language"],
        metadata_json=json.dumps(ai_result["explainable_factors"])
    )
    db.add(bot_msg_db)
    db.commit()

    return {
        "reply": ai_result["reply"],
        "detected_language": ai_result["detected_language"],
        "confidence_score": ai_result["confidence_score"],
        "is_off_topic": ai_result.get("is_off_topic", False),
        "timestamp": bot_msg_db.timestamp,
        "explainable_factors": ai_result["explainable_factors"]
    }

@router.get("/history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches user chat history with metadata"""
    msgs = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.timestamp.asc()).limit(50).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "language": m.language,
            "metadata": json.loads(m.metadata_json) if m.metadata_json else {},
            "timestamp": m.timestamp.isoformat()
        }
        for m in msgs
    ]
