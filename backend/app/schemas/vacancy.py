from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VacancyCreate(BaseModel):
    title: str = Field(..., description='Название вакансии')
    position: str = Field(..., description='Позиция (например, Backend Developer)')
    language: str = Field(..., description='Язык программирования')
    grade: str = Field(..., description='Грейд (junior, middle, senior)')
    ideal_resume: str = Field(..., description='Идеальное резюме')


class VacancyUpdate(BaseModel):
    title: str | None = None
    position: str | None = None
    language: str | None = None
    grade: str | None = None
    ideal_resume: str | None = None


class VacancyRead(BaseModel):
    id: uuid.UUID
    title: str
    position: str
    language: str
    grade: str
    ideal_resume: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    vacancy_id: uuid.UUID = Field(..., description='ID вакансии')


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., description='Новый статус заявки')


class ApplicationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    vacancy_id: uuid.UUID
    ml_score: float | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    time_limit_minutes: int
    created_at: datetime
    updated_at: datetime
    vacancy: VacancyRead | None = None  # Информация о вакансии
    user: dict | None = None  # Информация о пользователе (для модератора)

    class Config:
        from_attributes = True

