"""Скрипт для создания дефолтного модератора"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_session
from app.services.moderator_auth import create_moderator


async def main():
    """Создать дефолтного модератора"""
    async for session in get_session():
        try:
            moderator = await create_moderator(
                session,
                email='moderator@example.com',
                password='moderator'
            )
            await session.commit()
            print(f'✅ Модератор создан: {moderator.email}')
            print(f'   ID: {moderator.id}')
        except ValueError as e:
            print(f'⚠️  {e}')
            # Если модератор уже существует, это нормально
        except Exception as e:
            print(f'❌ Ошибка: {e}')
            await session.rollback()


if __name__ == '__main__':
    asyncio.run(main())

