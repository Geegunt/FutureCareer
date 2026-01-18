"""Seed a clean database with starter vacancies and questions."""

import asyncio
import sys
from pathlib import Path

# Make backend package importable when running directly
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.database import async_session_factory, engine
from app.models import Base, Question, Vacancy, Task
from scripts.init_data import create_admin_user, create_default_moderator
import json

async def reset_schema() -> None:
    """Drop and recreate every table to keep the DB in sync without Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy import select


SEED_VACANCIES = [
    {
        'title': 'Python Backend Starter',
        'position': 'Backend Developer',
        'language': 'python',
        'grade': 'junior',
        'ideal_resume': (
            'Опыт с FastAPI или Django, понимание SQL и Git. '
            'Готовность работать с асинхронным кодом и Docker.'
        ),
        'questions': [
            {
                'text': 'Расскажите о проекте, где вы использовали FastAPI или Django.',
                'order': 1,
                'difficulty': 'easy',
            },
            {
                'text': 'Как вы организуете работу с базой данных в Python-проектах?',
                'order': 2,
                'difficulty': 'medium',
            },
        ],
    },
    {
        'title': 'Go Microservice Engineer',
        'position': 'Backend Developer',
        'language': 'go',
        'grade': 'middle',
        'ideal_resume': (
            'Знание goroutines и каналов, опыт написания REST/gRPC сервисов, '
            'понимание CI/CD и контейнеризации.'
        ),
        'questions': [
            {
                'text': 'Как вы отлаживаете и профилируете Go сервисы в проде?',
                'order': 1,
                'difficulty': 'medium',
            },
            {
                'text': 'Опишите подход к управлению конкуренцией в вашем последнем Go-проекте.',
                'order': 2,
                'difficulty': 'hard',
            },
        ],
    },
    {
        'title': 'TypeScript Full-Stack',
        'position': 'Full-Stack Developer',
        'language': 'typescript',
        'grade': 'middle',
        'ideal_resume': (
            'Опыт с React/Vite на фронте и Node.js/NestJS на бэке, '
            'знание современных практик тестирования и SSR.'
        ),
        'questions': [
            {
                'text': 'Как вы организуете совместимый код между фронтендом и Node.js?',
                'order': 1,
                'difficulty': 'medium',
            },
            {
                'text': 'Расскажите про ваш пайплайн сборки и деплоя фронтенда.',
                'order': 2,
                'difficulty': 'easy',
            },
        ],
    },
]


async def seed_vacancies() -> None:
    async with async_session_factory() as session:
        for entry in SEED_VACANCIES:
            vacancy = await session.scalar(
                select(Vacancy).where(Vacancy.title == entry['title'])
            )
            if vacancy:
                vacancy.position = entry['position']
                vacancy.language = entry['language']
                vacancy.grade = entry['grade']
                vacancy.ideal_resume = entry['ideal_resume']
                print(f'⚙️  Обновлена вакансия: {vacancy.title}')
            else:
                vacancy = Vacancy(
                    title=entry['title'],
                    position=entry['position'],
                    language=entry['language'],
                    grade=entry['grade'],
                    ideal_resume=entry['ideal_resume'],
                )
                session.add(vacancy)
                await session.flush()
                print(f'✅ Создана вакансия: {vacancy.title}')

            for question_data in entry['questions']:
                existing_question = await session.scalar(
                    select(Question).where(
                        Question.text == question_data['text'],
                        Question.vacancy_id == vacancy.id,
                    )
                )
                if existing_question:
                    existing_question.order = question_data['order']
                    existing_question.difficulty = question_data['difficulty']
                    print(f'   ↺ Обновлен вопрос: {question_data["text"][:40]}...')
                else:
                    question = Question(
                        text=question_data['text'],
                        order=question_data['order'],
                        difficulty=question_data['difficulty'],
                        question_type='text',
                        vacancy_id=vacancy.id,
                    )
                    session.add(question)
                    print(f'   ➕ Добавлен вопрос: {question_data["text"][:40]}...')

        await session.commit()
        print('\n🎉 Seed завершен.')


async def seed_tasks() -> None:
    """Создает начальные задачи для каждой вакансии"""
    async with async_session_factory() as session:
        vacancies = await session.scalars(select(Vacancy))
        
        for vacancy in vacancies:
            # Создаем по 3 задачи разной сложности для каждой вакансии
            difficulties = ['easy', 'medium', 'hard']
            
            for difficulty in difficulties:
                task_title = f"Задача {difficulty} для {vacancy.title}"
                
                existing = await session.scalar(
                    select(Task).where(
                        Task.title == task_title,
                        Task.vacancy_id == vacancy.id
                    )
                )
                
                if not existing:
                    # Простые тестовые данные - задачи будут генерироваться ML при запросе
                    task = Task(
                        title=task_title,
                        description=f"Это тестовая задача уровня {difficulty}. Реальная задача будет сгенерирована ML сервисом.",
                        topic="general",
                        difficulty=difficulty,
                        open_tests=json.dumps([
                            {"input": "1 2", "output": "3"},
                            {"input": "5 10", "output": "15"}
                        ]),
                        hidden_tests=json.dumps([
                            {"input": "100 200", "output": "300"},
                            {"input": "-5 5", "output": "0"}
                        ]),
                        vacancy_id=vacancy.id,
                    )
                    session.add(task)
                    print(f'   ✅ Создана задача: {task_title}')
        
        await session.commit()
        print('\n🎉 Задачи созданы.')


async def main():
    print('--- Полный сброс схемы ---')
    await reset_schema()
    print('--- Старт сидирования ---')
    await seed_vacancies()
    # print('--- Создаем задачи ---')
    # await seed_tasks()  # Отключено: задачи генерируются через ML сервис
    print('--- Создаем админа ---')
    await create_admin_user()
    print('--- Создаем модератора ---')
    await create_default_moderator()


if __name__ == '__main__':
    asyncio.run(main())


