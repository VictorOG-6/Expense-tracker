from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from models import UserRead, User, UserCreate, password_hash, AuthModel
from database import SessionDep
from services.access_token import get_current_user
from routers.auth import create_tokens_for_user

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("", response_model=AuthModel, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: SessionDep):
    existing_user = session.exec(select(User).where(User.email == user.email)).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already reistered"
        )

    hashed_pwd = password_hash.hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_pwd)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    access_token, refresh_token = create_tokens_for_user(new_user, session)

    return {
        "user": new_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("", response_model=UserRead)
def get_user(current_user: User = Depends(get_current_user)):
    return current_user
