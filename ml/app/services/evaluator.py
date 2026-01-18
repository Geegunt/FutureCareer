from app.services.code_executor import code_executor
from app.core.config import settings
from app.services.llm_client import llm_client
from app.models.schemas import EvaluationRequest, EvaluationResult

class Evaluator:
    """Оценщик кода."""
    
    async def evaluate_submission(self, request: EvaluationRequest) -> EvaluationResult:
        """Оценивает решение кандидата.
        
        Args:
            request: Запрос с кодом, описанием задачи и скрытыми тестами
            
        Returns:
            EvaluationResult: Результат оценки с метриками и обратной связью
        """
        execution_results = code_executor.execute(request.code, request.hidden_tests)
        
        prompt = self._build_evaluation_prompt(request, execution_results)
        
        analysis = await llm_client.generate_json(
            model=settings.MODEL_CODER,
            messages=[
                {"role": "system", "content": "Ты эксперт по ревью кода и оценке решений алгоритмических задач. Всегда отвечай на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        return EvaluationResult(
            correctness_score=analysis.get("correctness_score", 0.0),
            efficiency_score=analysis.get("efficiency_score", 0.0),
            clean_code_score=analysis.get("clean_code_score", 0.0),
            feedback=analysis.get("feedback", "Обратная связь не предоставлена."),
            passed=analysis.get("correctness_score", 0.0) == 1.0
        )

    def _build_evaluation_prompt(self, request: EvaluationRequest, results: list) -> str:
        """Формирует промпт для оценки кода.
        
        Args:
            request: Запрос на оценку
            results: Результаты выполнения тестов
            
        Returns:
            str: Промпт для LLM
        """
        results_str = ""
        for r in results:
            results_str += f"Input: {r['input']}\nOutput: {r['output']}\nError: {r['error']}\n\n"
            
        return f"""
        Оцени следующее решение алгоритмической задачи.
        
        Описание задачи:
        {request.task_description}
        
        Сложность: {request.task_difficulty}
        
        Код пользователя:
        ```python
        {request.code}
        ```
        
        Результаты выполнения (скрытые тесты):
        {results_str}
        
        Проанализируй корректность, эффективность и качество кода:
        - Корректность: Проверь, соответствуют ли выходные данные ожидаемой логике задачи. Если есть ошибки, поставь 0.
        - Эффективность: Оптимальна ли временная сложность для данного уровня сложности?
        - Качество кода: Читаемый ли код, следует ли pythonic-стилю?
        
        ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста. Обратная связь должна быть НА РУССКОМ ЯЗЫКЕ.
        
        Формат JSON:
        {{
            "correctness_score": float (от 0.0 до 1.0),
            "efficiency_score": float (от 0.0 до 1.0),
            "clean_code_score": float (от 0.0 до 1.0),
            "feedback": "string (конструктивная обратная связь на русском языке)"
        }}
        """

evaluator = Evaluator()
