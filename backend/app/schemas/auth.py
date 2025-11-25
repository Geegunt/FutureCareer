from pydantic import BaseModel, EmailStr, Field

from .user import UserRead


class AuthCodeRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)


class AuthCodeVerify(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class AuthSuccessResponse(TokenResponse):
    user: UserRead


