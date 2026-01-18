class ScoringService:
    """Сервис расчёта итогового балла."""
    
    def calculate_final_score(
        self,
        difficulty: str,
        tests_passed: int,
        total_tests: int,
        time_taken_seconds: float,
        code_quality_score: float,  # 0-100
        communication_score: float,  # 0-100
        hints_used: list = None  # Список использованных подсказок
    ) -> float:
        """Рассчитывает итоговый балл по формуле.
        
        Args:
            difficulty: Уровень сложности задачи
            tests_passed: Количество пройденных тестов
            total_tests: Общее количество тестов
            time_taken_seconds: Время выполнения в секундах
            code_quality_score: Оценка качества кода (0-100)
            communication_score: Оценка коммуникации (0-100)
            hints_used: Список использованных подсказок
            
        Returns:
            float: Итоговый балл (0.0-100.0)
        """
        
        if hints_used is None:
            hints_used = []
        
        correctness = tests_passed / total_tests if total_tests > 0 else 0.0
        code_quality = code_quality_score / 100.0
        communication = communication_score / 100.0
        
        time_limits = {
            "easy": 300,    # 5 минут
            "medium": 600,  # 10 минут
            "hard": 900     # 15 минут
        }
        
        time_limit = time_limits.get(difficulty, 600)
        time_score = max(0.0, 1.0 - (time_taken_seconds / time_limit) * 0.5)
        
        difficulty_multiplier = {
            "easy": 1.0,
            "medium": 1.2,
            "hard": 1.5
        }
        multiplier = difficulty_multiplier.get(difficulty, 1.0)
        
        score = (
            0.40 * correctness +      # 40% - корректность
            0.20 * code_quality +     # 20% - качество кода
            0.20 * communication +    # 20% - коммуникация
            0.20 * time_score
        )
        
        final_score = score * multiplier * 100.0
        
        hint_penalties = {
            "surface": 5.0,   # -5 баллов
            "medium": 15.0,   # -15 баллов
            "deep": 30.0      # -30 баллов
        }
        
        total_hint_penalty = sum(hint_penalties.get(hint, 0.0) for hint in hints_used)
        final_score -= total_hint_penalty
        
        return max(0.0, min(100.0, final_score))

scoring_service = ScoringService()
