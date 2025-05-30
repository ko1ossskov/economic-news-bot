import openai
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_llm7_api():
    try:
        client = openai.OpenAI(
            base_url="https://api.llm7.io/v1",
            api_key="unused"
        )

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": "Привет! Ответь одним предложением."}],
            temperature=0.3
        )

        answer = response.choices[0].message.content
        logger.info(f"API работает! Ответ: {answer}")
        return True

    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        return False


if __name__ == "__main__":
    test_llm7_api()