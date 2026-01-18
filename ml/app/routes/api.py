from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    TaskGenerationRequest, Task,
    EvaluationRequest, EvaluationResult,
    AdaptiveLevelRequest, AdaptiveLevelResponse,
    CommunicationRequest, CommunicationResponse,
    FollowUpRequest, ScoringRequest, ScoringResponse,
    GenerateHintsRequest, GenerateHintsResponse
)
from app.services.task_generator import task_generator
from app.services.evaluator import evaluator
from app.services.adaptive_engine import adaptive_engine
from app.services.communication import communication_service
from app.services.scoring import scoring_service
from app.services.anti_cheat import anti_cheat_service
from app.services.hint_service import hint_service
from pydantic import BaseModel

router = APIRouter()

class AntiCheatRequest(BaseModel):
    """Запрос на проверку кода."""
    code: str
    problem_description: str

@router.post("/generate-task", response_model=Task)
async def generate_task(request: TaskGenerationRequest):
    """Генерирует новую задачу.
    
    Args:
        request: Запрос на генерацию задачи
        
    Returns:
        Task: Сгенерированная задача
    """
    try:
        task = await task_generator.generate_task(request.difficulty, language=request.language)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_solution(request: EvaluationRequest):
    """Оценивает решение кода.
    
    Args:
        request: Запрос на оценку
        
    Returns:
        EvaluationResult: Результат оценки
    """
    try:
        result = await evaluator.evaluate_submission(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adaptive-engine", response_model=AdaptiveLevelResponse)
async def get_next_level(request: AdaptiveLevelRequest):
    """Определяет следующий уровень сложности.
    
    Args:
        request: Запрос с результатами
        
    Returns:
        AdaptiveLevelResponse: Следующий уровень
    """
    try:
        result = adaptive_engine.determine_next_level(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/communication/evaluate", response_model=CommunicationResponse)
async def evaluate_communication(request: CommunicationRequest):
    """Оценивает объяснение решения.
    
    Args:
        request: Запрос на оценку коммуникации
        
    Returns:
        CommunicationResponse: Результат оценки
    """
    try:
        result = await communication_service.evaluate_explanation(
            request.problem_description,
            request.user_explanation,
            request.code
        )
        return CommunicationResponse(
            communication_score=result.get("communication_score", 0.0),
            feedback=result.get("feedback", "Обратная связь не предоставлена")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/communication/follow-up")
async def get_follow_up(request: FollowUpRequest):
    """Генерирует дополнительный вопрос.
    
    Args:
        request: Запрос на генерацию вопроса
        
    Returns:
        dict: Дополнительный вопрос
    """
    try:
        question = await communication_service.generate_followup_question(
            request.problem_description,
            request.code
        )
        return {"question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score", response_model=ScoringResponse)
async def calculate_score(request: ScoringRequest):
    """Рассчитывает итоговый балл.
    
    Args:
        request: Запрос на расчет балла
        
    Returns:
        ScoringResponse: Итоговый балл
    """
    try:
        final_score = scoring_service.calculate_final_score(
            difficulty=request.difficulty,
            tests_passed=request.tests_passed,
            total_tests=request.total_tests,
            time_taken_seconds=request.time_taken_seconds,
            code_quality_score=request.code_quality_score,
            communication_score=request.communication_score,
            hints_used=request.hints_used
        )
        return ScoringResponse(final_score=final_score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anti-cheat/check")
async def check_cheat(request: AntiCheatRequest):
    """Проверяет код на плагиат.
    
    Args:
        request: Запрос на проверку
        
    Returns:
        dict: Результат проверки
    """
    try:
        result = await anti_cheat_service.check_submission(request.code, request.problem_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-task-mock", response_model=Task)
async def generate_task_mock(request: TaskGenerationRequest):
    """Генерирует mock задачу.
    
    Args:
        request: Запрос на генерацию
        
    Returns:
        Task: Mock задача
    """
    base_examples = [
        {"input": "5\n1 3 7 2 9", "output": "9"},
        {"input": "3\n-1 -5 -2", "output": "-1"},
        {"input": "4\n10 10 10 10", "output": "10"},
    ]
    hidden_tests_full = [
        {"input": "10\n1 2 3 4 5 6 7 8 9 10", "output": "10"},
        {"input": "1\n42", "output": "42"},
        {"input": "6\n-1 -2 -3 -4 -5 -6", "output": "-1"},
        {"input": "8\n100 3 55 77 120 33 64 12", "output": "120"},
        {"input": "3\n0 0 0", "output": "0"},
        {"input": "7\n-10 0 -5 -3 -2 -11 -1", "output": "0"},
        {"input": "5\n999 -200 400 500 600", "output": "999"},
        {"input": "5\n-3 -3 -3 -3 -3", "output": "-3"},
        {"input": "2\n123456 987654", "output": "987654"},
        {"input": "9\n5 4 3 2 1 0 -1 -2 -3", "output": "5"},
        {"input": "4\n-1000000000 5 6 7", "output": "7"},
        {"input": "3\n-100 -50 -100", "output": "-50"},
        {"input": "6\n11 22 33 44 55 66", "output": "66"},
        {"input": "6\n-11 -22 -33 -44 -55 -6", "output": "-6"},
        {"input": "8\n7 7 7 7 8 8 8 8", "output": "8"},
    ]
    target_language = (request.language or 'python').lower()
    supported_languages = {'python', 'go', 'java', 'typescript'}
    if target_language not in supported_languages:
        target_language = 'python'
    canonical_solution_python = """import sys

def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    nums = list(map(int, data[1:1+n]))
    print(max(nums))

if __name__ == "__main__":
    main()
"""
    canonical_solutions = {
        "python": canonical_solution_python,
        "go": """package main

import (
    "bufio"
    "fmt"
    "math"
    "os"
)

func main() {
    reader := bufio.NewReader(os.Stdin)
    var n int
    if _, err := fmt.Fscan(reader, &n); err != nil {
        return
    }
    maxVal := math.MinInt32
    for i := 0; i < n; i++ {
        var x int
        fmt.Fscan(reader, &x)
        if x > maxVal {
            maxVal = x
        }
    }
    fmt.Println(maxVal)
}
""",
        "java": """import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws Exception {
        FastScanner fs = new FastScanner(System.in);
        int n;
        try {
            n = fs.nextInt();
        } catch (Exception e) {
            return;
        }
        int maxVal = Integer.MIN_VALUE;
        for (int i = 0; i < n; i++) {
            int value = fs.nextInt();
            if (value > maxVal) {
                maxVal = value;
            }
        }
        System.out.println(maxVal);
    }

    private static class FastScanner {
        private final InputStream in;
        private final byte[] buffer = new byte[1 << 16];
        private int ptr = 0, len = 0;

        FastScanner(InputStream is) {
            this.in = is;
        }

        private int read() throws IOException {
            if (ptr >= len) {
                len = in.read(buffer);
                ptr = 0;
                if (len <= 0) {
                    return -1;
                }
            }
            return buffer[ptr++];
        }

        int nextInt() throws IOException {
            int c;
            while ((c = read()) != -1 && c <= ' ') {
            }
            if (c == -1) {
                throw new IOException();
            }
            int sign = 1;
            if (c == '-') {
                sign = -1;
                c = read();
            }
            int val = 0;
            while (c > ' ') {
                val = val * 10 + c - '0';
                c = read();
            }
            return val * sign;
        }
    }
}
""",
        "typescript": """import * as fs from 'fs';

const data = fs.readFileSync(0, 'utf8').trim().split(/\\s+/).map(Number);
if (data.length === 0) {
  process.exit(0);
}
const n = data[0];
let maxVal = -Infinity;
for (let i = 1; i <= n && i < data.length; i++) {
  if (data[i] > maxVal) {
    maxVal = data[i];
  }
}
console.log(maxVal.toString());
""",
    }
    mock_task = Task(
        title="Найти максимальный элемент в массиве",
        description="Дан массив целых чисел. Найдите максимальный элемент в массиве.",
        input_format="Первая строка содержит число n - размер массива. Вторая строка содержит n целых чисел через пробел.",
        output_format="Выведите максимальный элемент массива.",
        examples=base_examples,
        constraints=["1 ≤ n ≤ 1000", "-10^9 ≤ элементы массива ≤ 10^9"],
        difficulty=request.difficulty,
        hidden_tests=[case["input"] for case in hidden_tests_full],
        hidden_tests_full=hidden_tests_full,
        canonical_solution=canonical_solutions.get(target_language, canonical_solution_python),
        canonical_solutions=canonical_solutions,
    )
    return mock_task

@router.post("/hints/generate", response_model=GenerateHintsResponse)
async def generate_hints(request: GenerateHintsRequest):
    """Генерирует подсказки для задачи.
    
    Args:
        request: Запрос на генерацию подсказок
        
    Returns:
        GenerateHintsResponse: Подсказки
    """
    try:
        hints = await hint_service.generate_hints(
            task_description=request.task_description,
            task_difficulty=request.task_difficulty,
            input_format=request.input_format,
            output_format=request.output_format,
            examples=[ex.dict() for ex in request.examples]
        )
        return GenerateHintsResponse(hints=hints)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
