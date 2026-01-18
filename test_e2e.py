#!/usr/bin/env python3
"""E2E тест для проверки работы всех сервисов EXALAA"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"
ML_URL = "http://localhost:8002"
EXECUTOR_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:5173"

def test_health_endpoints():
    """Проверка health endpoints всех сервисов"""
    print("🔍 Проверка health endpoints...")
    
    services = {
        "Backend": f"{BASE_URL}/health",
        "ML Service": f"{ML_URL}/health",
        "Executor": f"{EXECUTOR_URL}/health",
        "Frontend": FRONTEND_URL,
    }
    
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: OK")
            else:
                print(f"  ❌ {name}: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            return False
    
    return True

def test_swagger_api():
    """Проверка доступности Swagger API"""
    print("\n🔍 Проверка Swagger API...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200 and "swagger" in response.text.lower():
            print("  ✅ Swagger API доступен")
            return True
        else:
            print("  ❌ Swagger API недоступен")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_openapi_schema():
    """Проверка OpenAPI схемы"""
    print("\n🔍 Проверка OpenAPI схемы...")
    
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            print(f"  ✅ OpenAPI схема загружена")
            print(f"  📊 Найдено endpoints: {len(schema.get('paths', {}))}")
            return True
        else:
            print("  ❌ OpenAPI схема недоступна")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_vacancies_endpoint():
    """Проверка endpoint вакансий"""
    print("\n🔍 Проверка endpoint вакансий...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/vacancies", timeout=5)
        if response.status_code == 200:
            vacancies = response.json()
            print(f"  ✅ Вакансии загружены: {len(vacancies)} шт.")
            if vacancies:
                print(f"  📋 Пример: {vacancies[0].get('title', 'N/A')}")
            return True
        else:
            print(f"  ❌ Ошибка: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_ml_service():
    """Проверка ML сервиса"""
    print("\n🔍 Проверка ML сервиса...")
    
    try:
        response = requests.get(f"{ML_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ ML сервис работает")
            return True
        else:
            # Пробуем альтернативный endpoint
            response = requests.get(f"{ML_URL}/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ ML сервис работает")
                return True
            print(f"  ❌ ML сервис недоступен: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def test_executor_service():
    """Проверка Executor сервиса"""
    print("\n🔍 Проверка Executor сервиса...")
    
    try:
        response = requests.get(f"{EXECUTOR_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Executor работает: {data}")
            return True
        else:
            print(f"  ❌ Executor недоступен: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False

def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🚀 E2E ТЕСТИРОВАНИЕ ПРОЕКТА EXALAA")
    print("=" * 60)
    
    tests = [
        ("Health Endpoints", test_health_endpoints),
        ("Swagger API", test_swagger_api),
        ("OpenAPI Schema", test_openapi_schema),
        ("Vacancies Endpoint", test_vacancies_endpoint),
        ("ML Service", test_ml_service),
        ("Executor Service", test_executor_service),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Критическая ошибка в тесте '{name}': {e}")
            results.append((name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"Результат: {passed}/{total} тестов пройдено")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print(f"\n⚠️  ПРОВАЛЕНО ТЕСТОВ: {total - passed}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
