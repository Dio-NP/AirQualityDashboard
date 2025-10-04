from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import Session
from datetime import timedelta
from db import get_session, init_db
from auth import User, get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@router.on_event("startup")
def _startup():
    init_db()


@router.post('/auth/register')
def register(payload: RegisterRequest):
    with get_session() as s:
        existing = s.exec(User.select().where(User.email == str(payload.email))).first() if hasattr(User, 'select') else None
        # Fallback select
        if existing is None:
            from sqlmodel import select
            existing = s.exec(select(User).where(User.email == str(payload.email))).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = User(email=str(payload.email), hashed_password=get_password_hash(payload.password))
        s.add(user)
        s.commit()
        s.refresh(user)
        return {"id": user.id}


@router.post('/auth/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(User.select().where(User.email == form_data.username)).first() if hasattr(User, 'select') else None
    if user is None:
        from sqlmodel import select
        user = session.exec(select(User).where(User.email == form_data.username)).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get('/auth/me')
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}
