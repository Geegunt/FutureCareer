import httpx
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings

class LLMClient:
    """Клиент для работы с LLM моделями."""
    
    def __init__(self):
        """Инициализирует клиент с API ключом и базовым URL."""
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.SCIBOX_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.verify_ssl = True

    async def generate(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False
    ) -> str:
        """Генерирует текстовый ответ от LLM.
        
        Args:
            model: Название модели
            messages: Список сообщений для чата
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов
            json_mode: Режим JSON ответа
            
        Returns:
            str: Сгенерированный текст
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            try:
                print(f"🔗 Отправляем запрос к: {self.base_url}/chat/completions")
                print(f"🔑 API ключ: {self.api_key[:20]}...")
                print(f"🔒 SSL проверка: {self.verify_ssl}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions", 
                    headers=self.headers, 
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.ConnectError as e:
                error_msg = f"Не удается подключиться к Groq API. Проверьте интернет соединение. URL: {self.base_url}. Ошибка: {e}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            except httpx.HTTPStatusError as e:
                error_msg = f"API вернул HTTP ошибку {e.response.status_code}: {e.response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            except httpx.TimeoutException as e:
                error_msg = f"Таймаут при обращении к LLM API: {e}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Неожиданная ошибка LLM клиента ({type(e).__name__}): {e}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)

    async def generate_json(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Генерирует JSON ответ от LLM.
        
        Args:
            model: Название модели
            messages: Список сообщений
            temperature: Температура генерации
            
        Returns:
            Dict[str, Any]: Спарсенный JSON ответ
        """
        if messages and "json" not in messages[-1].get("content", "").lower():
             messages[-1]["content"] += "\n\nPlease respond with valid JSON."

        content = await self.generate(model, messages, temperature, json_mode=True)
        
        print(f"📝 Получен ответ от LLM (первые 500 символов): {content[:500]}")
        
        if "<think>" in content:
            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            print(f"🧹 Удалены теги <think>, новая длина: {len(content)}")
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        try:
            parsed = json.loads(content)
            print(f"✅ JSON успешно распарсен, ключи: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
            
            if isinstance(parsed, dict) and 'content' in parsed and isinstance(parsed['content'], str):
                print(f"🔄 Обнаружен вложенный JSON в поле 'content', извлекаем...")
                try:
                    parsed = json.loads(parsed['content'])
                    print(f"✅ Вложенный JSON распарсен, ключи: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
                except json.JSONDecodeError:
                    print(f"⚠️ Не удалось распарсить вложенный JSON, используем исходный")
            
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ Не удалось распарсить JSON: {e}")
            print(f"📄 Полный контент: {content}")
            raise ValueError("Модель не вернула корректный JSON")

llm_client = LLMClient()
