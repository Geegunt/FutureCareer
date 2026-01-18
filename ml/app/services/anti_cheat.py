from app.core.config import settings
from app.services.llm_client import llm_client

class AntiCheatService:
    """Сервис проверки кода на плагиат."""
    
    async def check_submission(self, code: str, problem_desc: str) -> dict:
        """Проверяет код на признаки нечестного решения.
        
        Args:
            code: Код кандидата
            problem_desc: Описание задачи
            
        Returns:
            dict: Результат проверки
        """
        prompt = f"""
        Проанализируй следующий код на признаки нечестного решения, плагиата или чистой AI-генерации без понимания.
        
        Задача: {problem_desc}
        Код: {code}
        
        Обрати внимание на:
        - Комментарии, которые выглядят скопированными из другого контекста
        - Имена переменных, которые слишком общие или идентичны стандартным туториалам
        - Логику, которая решает другую версию задачи
        
        ВАЖНО: Верни ТОЛЬКО валидный JSON. Причина должна быть НА РУССКОМ ЯЗЫКЕ.
        
        Формат JSON:
        {{
            "is_suspicious": bool,
            "confidence": float (от 0.0 до 1.0),
            "reason": "string (на русском языке)"
        }}
        """
        
        return await llm_client.generate_json(
            model=settings.MODEL_AWQ,
            messages=[
                {"role": "system", "content": "Ты специалист по проверке целостности кода и обнаружению плагиата. Всегда отвечай на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

anti_cheat_service = AntiCheatService()
