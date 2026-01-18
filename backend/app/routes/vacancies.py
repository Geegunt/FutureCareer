"""Роуты для работы с вакансиями"""

import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..dependencies.auth import get_current_user
from ..models import Application, Question, User, Vacancy
from ..schemas import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate, QuestionRead, VacancyRead

router = APIRouter(prefix='/vacancies', tags=['vacancies'])


@router.get('', response_model=list[VacancyRead])
async def list_vacancies(
    language: str | None = None,
    grade: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Получить список вакансий с фильтрацией по языку и грейду"""
    try:
        query = select(Vacancy)
        
        if language:
            query = query.where(Vacancy.language == language)
        if grade:
            query = query.where(Vacancy.grade == grade)
        
        result = await session.scalars(query.order_by(Vacancy.created_at.desc()))
        vacancies = list(result.all())
        
        # Убеждаемся, что все вакансии правильно сериализуются
        return [VacancyRead.model_validate(v) for v in vacancies]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in list_vacancies: {e}', exc_info=True)
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при загрузке вакансий: {str(e)}'
        )


@router.get('/{vacancy_id}', response_model=VacancyRead)
async def get_vacancy(
    vacancy_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Получить вакансию по ID"""
    vacancy = await session.get(Vacancy, vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found'
        )
    return vacancy


@router.post('/{vacancy_id}/apply', response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def apply_to_vacancy(
    vacancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Подать заявку на вакансию. Если заявка уже существует, возвращает существующую."""
    try:
        from sqlalchemy.orm import selectinload
        
        vacancy = await session.get(Vacancy, vacancy_id)
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found'
            )
        
        # Проверяем, нет ли уже заявки
        stmt = (
            select(Application)
            .where(
                Application.user_id == current_user.id,
                Application.vacancy_id == vacancy_id
            )
            .options(selectinload(Application.vacancy))
        )
        existing = await session.scalar(stmt)
        
        if existing:
            # Если заявка уже существует и тест пройден, запрещаем повторную подачу
            if existing.status in ['survey_completed', 'algo_test_completed', 'final_verdict', 'under_review', 'accepted', 'rejected']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Вы уже проходили тест по этой вакансии.'
                )
            # Если заявка существует, но тест не пройден, возвращаем её
            await session.refresh(existing)
            # Создаем ApplicationRead без поля user (оно не нужно для обычных пользователей)
            app_dict = {
                'id': existing.id,
                'user_id': existing.user_id,
                'vacancy_id': existing.vacancy_id,
                'ml_score': existing.ml_score,
                'status': existing.status,
                'started_at': existing.started_at,
                'completed_at': existing.completed_at,
                'time_limit_minutes': existing.time_limit_minutes,
                'created_at': existing.created_at,
                'updated_at': existing.updated_at,
                'vacancy': existing.vacancy,
                'user': None,  # Не включаем данные пользователя для обычных запросов
            }
            return ApplicationRead.model_validate(app_dict)
        
        # Создаём новую заявку
        application = Application(
            user_id=current_user.id,
            vacancy_id=vacancy_id,
            status='pending',
        )
        session.add(application)
        await session.commit()
        await session.refresh(application)
        
        # Загружаем вакансию для сериализации
        await session.refresh(application, ['vacancy'])
        
        # Создаем ApplicationRead без поля user
        app_dict = {
            'id': application.id,
            'user_id': application.user_id,
            'vacancy_id': application.vacancy_id,
            'ml_score': application.ml_score,
            'status': application.status,
            'started_at': application.started_at,
            'completed_at': application.completed_at,
            'time_limit_minutes': application.time_limit_minutes,
            'created_at': application.created_at,
            'updated_at': application.updated_at,
            'vacancy': application.vacancy,
            'user': None,  # Не включаем данные пользователя для обычных запросов
        }
        return ApplicationRead.model_validate(app_dict)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in apply_to_vacancy: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при подаче заявки: {str(e)}'
        )


@router.patch('/applications/{application_id}/status', response_model=ApplicationRead)
async def update_application_status(
    application_id: uuid.UUID,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновить статус заявки"""
    try:
        from sqlalchemy.orm import selectinload
        
        # Загружаем заявку с вакансией
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(selectinload(Application.vacancy))
        )
        application = await session.scalar(stmt)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Application not found'
            )
        
        # Проверяем, что заявка принадлежит текущему пользователю
        if application.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail='Access denied'
            )
        
        # Валидация статуса
        valid_statuses = ['pending', 'survey_completed', 'algo_test_completed', 'final_verdict']
        if status_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            )
        
        application.status = status_data.status
        await session.commit()
        await session.refresh(application)
        
        # Создаем ApplicationRead без поля user
        app_dict = {
            'id': application.id,
            'user_id': application.user_id,
            'vacancy_id': application.vacancy_id,
            'ml_score': application.ml_score,
            'status': application.status,
            'created_at': application.created_at,
            'updated_at': application.updated_at,
            'vacancy': application.vacancy,
            'user': None,  # Не включаем данные пользователя для обычных запросов
        }
        return ApplicationRead.model_validate(app_dict)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error updating application status: {str(e)}'
        )


@router.get('/my/applications', response_model=list[ApplicationRead])
async def get_my_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить список заявок текущего пользователя с информацией о вакансиях"""
    try:
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(Application)
            .where(Application.user_id == current_user.id)
            .options(selectinload(Application.vacancy))
            .order_by(Application.created_at.desc())
        )
        result = await session.scalars(stmt)
        applications = list(result.all())
        
        # Создаем ApplicationRead без поля user (оно не нужно для обычных пользователей)
        result_list = []
        for app in applications:
            app_dict = {
                'id': app.id,
                'user_id': app.user_id,
                'vacancy_id': app.vacancy_id,
                'ml_score': app.ml_score,
                'status': app.status,
                'started_at': app.started_at,
                'completed_at': app.completed_at,
                'time_limit_minutes': app.time_limit_minutes,
                'created_at': app.created_at,
                'updated_at': app.updated_at,
                'vacancy': app.vacancy,
                'user': None,  # Не включаем данные пользователя для обычных запросов
            }
            result_list.append(ApplicationRead.model_validate(app_dict))
        
        return result_list
    except Exception as e:
        logger.error(f'Error in get_my_applications: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при загрузке заявок: {str(e)}'
        )


@router.get('/{vacancy_id}/survey-questions', response_model=list[QuestionRead])
async def get_survey_questions(
    vacancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить до 10 случайных вопросов для опроса по вакансии"""
    try:
        vacancy = await session.get(Vacancy, vacancy_id)
        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found'
            )
        
        # Получаем вопросы, привязанные к этой вакансии, или все вопросы, если нет привязки
        stmt = select(Question).where(
            (Question.vacancy_id == vacancy_id) | (Question.vacancy_id.is_(None))
        )
        all_questions = await session.scalars(stmt)
        questions_list = list(all_questions.all())
        
        if len(questions_list) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Нет вопросов в базе для этой вакансии'
            )
        
        # Выбираем случайные вопросы (до 10)
        random.shuffle(questions_list)
        selected_questions = questions_list[:10]
        
        # Убеждаемся, что все поля правильно сериализуются
        result = []
        for q in selected_questions:
            result.append(QuestionRead.model_validate(q))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in get_survey_questions: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при загрузке вопросов: {str(e)}'
        )


@router.get('/{vacancy_id}/tasks', response_model=list[QuestionRead])
async def get_random_tasks(
    vacancy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Получить 3 случайные задачи разной сложности для вакансии"""
    vacancy = await session.get(Vacancy, vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found'
        )
    
    # Получаем задачи, привязанные к этой вакансии, или все задачи, если нет привязки
    stmt = select(Question).where(
        (Question.vacancy_id == vacancy_id) | (Question.vacancy_id.is_(None))
    )
    all_questions = await session.scalars(stmt)
    questions_list = list(all_questions.all())
    
    # Убрана проверка на минимум 3 задачи - можно работать с любым количеством
    if len(questions_list) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Нет задач в базе для этой вакансии'
        )
    
    # Группируем задачи по сложности
    by_difficulty: dict[str, list[Question]] = {'easy': [], 'medium': [], 'hard': []}
    for q in questions_list:
        difficulty = q.difficulty or 'medium'
        if difficulty in by_difficulty:
            by_difficulty[difficulty].append(q)
    
    # Выбираем по одной задаче каждого уровня сложности
    selected_tasks: list[Question] = []
    for difficulty in ['easy', 'medium', 'hard']:
        if by_difficulty[difficulty]:
            selected_tasks.append(random.choice(by_difficulty[difficulty]))
    
    # Если не хватает задач, дополняем случайными
    while len(selected_tasks) < 3:
        remaining = [q for q in questions_list if q not in selected_tasks]
        if not remaining:
            break
        selected_tasks.append(random.choice(remaining))
    
    # Перемешиваем порядок
    random.shuffle(selected_tasks)
    
    return selected_tasks[:3]

