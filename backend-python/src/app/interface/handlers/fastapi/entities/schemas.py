"""Request / response bodies. JSON field names match the Go API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt only uses the first 72 bytes
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserRefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access: str
    refresh: str


class UserLoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    token: TokenResponse


class MonitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str


class DataResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: int
    data: dict[str, Any]
    message: str
    data_schema: dict[str, Any]


class DataListResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: int
    data: list[dict[str, Any]]
    page: int
    page_size: int
    total_page: int
    total_data: int
    message: str
    data_schema: dict[str, Any]
