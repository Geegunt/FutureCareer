from app.core.config import settings
from app.services.llm_client import llm_client
from app.models.schemas import Hint
from typing import List

class HintService:
    """Сервис генерации подсказок для задач."""
    
    PENALTY_SURFACE = 5.0
    PENALTY_MEDIUM = 15.0
    PENALTY_DEEP = 30.0
    
    async def generate_hints(
        self,
        task_description: str,
        task_difficulty: str,
        input_format: str,
        output_format: str,
        examples: List[dict]
    ) -> List[Hint]:
        """Генерирует три уровня подсказок для задачи.
        
        Args:
            task_description: Описание задачи
            task_difficulty: Уровень сложности
            input_format: Формат входных данных
            output_format: Формат выходных данных
            examples: Примеры входных/выходных данных
            
        Returns:
            List[Hint]: Список из трех подсказок разного уровня
        """
        
        examples_str = "\n".join([
            f"Вход: {ex.get('input', ex.get('input', ''))}\nВыход: {ex.get('output', ex.get('output', ''))}"
            for ex in examples
        ])
        
        prompt = f"""
        Сгенерируй ТРИ подсказки разного уровня для следующей алгоритмической задачи.
        
        Задача: {task_description}
        Сложность: {task_difficulty}
        Формат входа: {input_format}
        Формат выхода: {output_format}
        
        Примеры:
        {examples_str}
        
        Создай три подсказки:
        
        1. **ПОВЕРХНОСТНАЯ (surface)** - Общее направление, не раскрывая алгоритм:
           - Укажи на ключевую идею или паттерн
           - Не давай конкретных шагов реализации
           - Пример: "Подумай о том, как можно использовать хеш-таблицу для отслеживания..."
        
        2. **СРЕДНЯЯ (medium)** - Более конкретная, но без полного решения:
           - Опиши общий подход или структуру данных
           - Намекни на основные шаги алгоритма
           - Пример: "Используй словарь для подсчета частоты элементов, затем найди элемент с максимальной частотой"
        
        3. **ГЛУБОКАЯ (deep)** - Почти полное решение, но без кода:
           - Подробно опиши алгоритм шаг за шагом
           - Укажи на важные детали реализации
           - Пример: "1) Создай пустой словарь. 2) Пройди по массиву и для каждого элемента увеличь счетчик в словаре. 3) Найди ключ с максимальным значением..."
        
        ВАЖНО: 
        - Все подсказки должны быть НА РУССКОМ ЯЗЫКЕ.
        - КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать код (функции, переменные, синтаксис языка). Используй псевдокод или текстовое описание.
        - Каждая следующая подсказка должна быть более детальной.
        - Верни ТОЛЬКО валидный JSON объект.
        
        Формат JSON:
        {{
            "surface_hint": "текст поверхностной подсказки",
            "medium_hint": "текст средней подсказки",
            "deep_hint": "текст глубокой подсказки"
        }}
        """
        
        result = await llm_client.generate_json(
            model=settings.MODEL_AWQ,
            messages=[
                {"role": "system", "content": "Ты эксперт по созданию обучающих подсказок для алгоритмических задач. Всегда отвечай на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        hints = [
            Hint(
                level="surface",
                content=result.get("surface_hint", "Подсказка не сгенерирована"),
                penalty=self.PENALTY_SURFACE
            ),
            Hint(
                level="medium",
                content=result.get("medium_hint", "Подсказка не сгенерирована"),
                penalty=self.PENALTY_MEDIUM
            ),
            Hint(
                level="deep",
                content=result.get("deep_hint", "Подсказка не сгенерирована"),
                penalty=self.PENALTY_DEEP
            )
        ]
        
        return hints

hint_service = HintService()
