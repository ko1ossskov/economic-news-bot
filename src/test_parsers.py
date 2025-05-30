import logging
from news_parser import NewsParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_parsers():
    # Инициализируем парсер с тестовыми источниками
    test_sources = [
        {"name": "RBC", "url": "https://www.rbc.ru/economics/", "type": "rbc"},
        {"name": "РИА", "url": "https://sn.ria.ru", "type": "ria"}
    ]
    parser = NewsParser(test_sources)

    # Тест для RBC
    rbc_news = parser._parse_rbc(test_sources[0]["url"], test_sources[0]["name"])
    logger.info(f"RBC: получено {len(rbc_news)} новостей. Пример: {rbc_news[0]['title'][:50]}...")

    # Тест для РИА
    ria_news = parser._parse_ria(test_sources[1]["url"], test_sources[1]["name"])
    logger.info(f"РИА: получено {len(ria_news)} новостей. Пример: {ria_news[0]['title'][:50]}...")

if __name__ == "__main__":
    test_parsers()