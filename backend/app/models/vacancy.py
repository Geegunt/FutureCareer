import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Vacancy(Base):
    __tablename__ = 'vacancies'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Название вакансии
    position: Mapped[str] = mapped_column(String(255), nullable=False)  # Позиция (например, "Backend Developer")
    language: Mapped[str] = mapped_column(String(50), nullable=False)  # Язык программирования
    grade: Mapped[str] = mapped_column(String(50), nullable=False)  # Грейд (junior, middle, senior)
    ideal_resume: Mapped[str] = mapped_column(Text, nullable=False)  # Идеальное резюме (генерируется нейронкой)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    applications: Mapped[list['Application']] = relationship(
        back_populates='vacancy', cascade='all, delete-orphan'
    )
    questions: Mapped[list['Question']] = relationship(
        back_populates='vacancy', cascade='all, delete-orphan'
    )
    tasks: Mapped[list['Task']] = relationship(
        back_populates='vacancy', cascade='all, delete-orphan'
    )
    user_contest_tasks: Mapped[list['UserContestTasks']] = relationship(
        back_populates='vacancy', cascade='all, delete-orphan'
    )


class Application(Base):
    """Заявка пользователя на вакансию"""
    __tablename__ = 'applications'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey('vacancies.id', ondelete='CASCADE'), nullable=False
    )
    ml_score: Mapped[float | None] = mapped_column(default=None)  # Оценка от ML сервиса
    status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, completed, failed
    started_at: Mapped[datetime | None] = mapped_column(default=None)  # Время начала собеседования
    completed_at: Mapped[datetime | None] = mapped_column(default=None)  # Время завершения собеседования
    time_limit_minutes: Mapped[int] = mapped_column(default=120)  # Лимит времени в минутах
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped['User'] = relationship(back_populates='applications')
    vacancy: Mapped['Vacancy'] = relationship(back_populates='applications')

