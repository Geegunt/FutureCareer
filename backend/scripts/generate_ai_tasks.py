"""Генерация реальных задач через ML сервис (Groq AI)"""

import asyncio
import sys
from pathlib import Path

# Make backend package importable
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.database import async_session_factory
from app.models import Task, Vacancy
from sqlalchemy import select
import httpx
import json


ML_SERVICE_URL = "http://ml:8002/api/v1"


async def generate_task_via_ml(difficulty: str, language: str, topic: str = "algorithms"):
    """Генерирует задачу через ML сервис"""
    print(f"   🤖 Генерирую задачу: {difficulty}/{language}...", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/generate-task",
                json={
                    "difficulty": difficulty,
                    "language": language,
                    "topic": topic
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Задача сгенерирована: {data.get('title', 'Без названия')}", flush=True)
                return data
            else:
                print(f"   ❌ Ошибка ML API: {response.status_code} - {response.text}", flush=True)
                return None
                
        except Exception as e:
            print(f"   ❌ Ошибка при генерации: {e}", flush=True)
            return None


async def generate_tasks_for_vacancies():
    """Генерирует задачи для всех вакансий через Groq AI"""
    async with async_session_factory() as session:
        # Получаем все вакансии
        vacancies = await session.scalars(select(Vacancy))
        vacancies_list = list(vacancies.all())
        
        if not vacancies_list:
            print("❌ Нет вакансий в базе данных")
            return
        
        print(f"\n📋 Найдено вакансий: {len(vacancies_list)}\n")
        
        for vacancy in vacancies_list:
            print(f"🎯 Вакансия: {vacancy.title} ({vacancy.language})")
            
            # Удаляем старые заглушки-задачи для этой вакансии
            old_tasks = await session.scalars(
                select(Task).where(Task.vacancy_id == vacancy.id)
            )
            old_tasks_list = list(old_tasks.all())
            
            if old_tasks_list:
                print(f"   🗑️  Удаляю {len(old_tasks_list)} старых задач-заглушек...")
                for old_task in old_tasks_list:
                    await session.delete(old_task)
                await session.commit()
            
            # Генерируем 3 задачи разной сложности
            difficulties = ['easy', 'medium', 'hard']
            
            for difficulty in difficulties:
                # Генерируем задачу через ML
                task_data = await generate_task_via_ml(
                    difficulty=difficulty,
                    language=vacancy.language,
                    topic="algorithms"
                )
                
                if not task_data:
                    print(f"   ⚠️  Пропускаю {difficulty} - не удалось сгенерировать")
                    continue
                
                # Формируем полное описание задачи с форматами
                full_description = task_data.get('description', '')
                if task_data.get('input_format'):
                    full_description += f"\n\n**Формат входных данных:**\n{task_data['input_format']}"
                if task_data.get('output_format'):
                    full_description += f"\n\n**Формат выходных данных:**\n{task_data['output_format']}"
                if task_data.get('constraints'):
                    full_description += f"\n\n**Ограничения:**\n{task_data['constraints']}"
                
                # Создаем задачу в БД
                task = Task(
                    title=task_data.get('title', f'Задача {difficulty}'),
                    description=full_description,
                    topic=task_data.get('topic', 'algorithms'),
                    difficulty=difficulty,
                    open_tests=json.dumps(task_data.get('examples', [])),
                    hidden_tests=json.dumps(task_data.get('hidden_tests_full', [])),
                    canonical_solution=task_data.get('canonical_solution', ''),
                    hints=task_data.get('hints', []),
                    vacancy_id=vacancy.id,
                )
                
                session.add(task)
                print(f"   💾 Сохранена задача: {task.title}")
            
            await session.commit()
            print(f"   ✅ Завершено для {vacancy.title}\n")
        
        print("🎉 Все задачи успешно сгенерированы!")


async def main():
    print("=" * 60)
    print("🚀 Генерация задач через Groq AI")
    print("=" * 60)
    print("\n⚠️  Это может занять 2-3 минуты (генерация через LLM)\n")
    
    try:
        await generate_tasks_for_vacancies()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
