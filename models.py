from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.sql import func
from pwdlib import PasswordHash
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import EmailStr

password_hash = PasswordHash.recommended()


class GoogleUser(SQLModel):
    sub: str  # Google's unique user ID
    email: EmailStr
    email_verified: bool = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


class UserBase(SQLModel):
    name: str
    email: EmailStr


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    transactions: list["Transactions"] = Relationship(back_populates="owner")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": func.now()},
        nullable=False,
    )


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    transactions: list["Transactions"] = []


class Login(SQLModel):
    username: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str
    refresh_token: str


class TokenData(SQLModel):
    username: str | None = None
    user_id: int | None = None
    jti: str | None = None


class RefreshTokenRequest(SQLModel):
    refresh_token: str


class RefreshToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    revoked: bool = False


class AuthModel(SQLModel):
    user: UserRead
    access_token: str
    refresh_token: str
    token_type: str


class TransactionsType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionsBase(SQLModel):
    name: str
    price: int
    type: TransactionsType = TransactionsType.CREDIT


class Transactions(TransactionsBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: Optional["User"] = Relationship(back_populates="transactions")
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": func.now()},
        nullable=False,
    )


class TransactionsCreate(TransactionsBase):
    pass


class TransactionsRead(TransactionsBase):
    id: int


class TransactionsUpdate(SQLModel):
    name: str | None = None
    price: int | None = None
    type: TransactionsType | None = None
