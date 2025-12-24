from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from typing import Annotated
from datetime import datetime, timezone, timedelta
from models import Token, Login, User, password_hash, RefreshToken, RefreshTokenRequest, AuthModel
from database import SessionDep
from access_token import create_access_token, create_refresh_token, verify_token, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/auth", tags=["Auth"])

def create_tokens_for_user(user: User, session: SessionDep):
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    token_data = verify_token(refresh_token, "refresh", credentials_exception)

    db_refresh_token = RefreshToken(
        user_id=user.id,
        token=token_data.jti,
        expires_at=datetime.now(timezone.utc) + refresh_token_expires
    )
    session.add(db_refresh_token)
    session.commit()

    return access_token, refresh_token

@router.post("/login", response_model=AuthModel)
def login(request: Login, session: SessionDep):
    statement = select(User).where(User.email == request.username)
    user = session.exec(statement).first()

    if not user or not password_hash.verify(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Credentials", headers={"WWW-Authenticate": "Bearer"})
    
    access_token, refresh_token = create_tokens_for_user(user, session)

    return {"user": user, "access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()

    if not user or not password_hash.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials", headers={"WWW-Authenticate": "Bearer"})
    
    access_token, refresh_token = create_tokens_for_user(user, session)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_access_token(request: RefreshTokenRequest, session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data = verify_token(request.refresh_token, "refresh", credentials_exception)

    if not token_data:
        raise credentials_exception
    
    # Check if token is in database and not revoked
    db_token = session.exec(select(RefreshToken).where(RefreshToken.token == token_data.jti, RefreshToken.revoked == False)).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or does not exist"
        )
    
    # Check if token is expired
    if db_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    user = session.get(User, token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    db_token.revoked = True
    session.commit()

    # Create new tokens
    access_token, new_refresh_token = create_tokens_for_user(user, session)

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@router.post("/logout")
def logout(request: RefreshTokenRequest, session: SessionDep):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )
    
    token_data = verify_token(request.refresh_token, "refresh", credentials_exception)
    
    if not token_data:
        raise credentials_exception
    
    # Revoke the token
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == token_data.jti)
    ).first()
    
    if db_token:
        db_token.revoked = True
        session.commit()
    
    return {"message": "Successfully logged out"}