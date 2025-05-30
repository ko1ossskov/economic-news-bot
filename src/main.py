#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диалоговая система для анализа экономических новостей
Курсовая работа (оптимизированная версия)
"""

import os
import sys
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("economic_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Импорт модулей системы
try:
    from news_parser import NewsParser
    from news_analyzer import NewsAnalyzer
    from dialog_manager import DialogManager
    from dialog_interface import DialogInterface
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    sys.exit(1)


class EconomicNewsBot:
    """
    Оптимизированный класс диалоговой системы
    """

    def __init__(self, config_path="config.json"):
        """
        Улучшенная инициализация с обработкой ошибок
        """
        try:
            self.config = self._load_config(config_path)
            if not self.config:
                raise ValueError("Не удалось загрузить конфигурацию")

            self.news_sources = self.config.get("news_sources", [])
            self.llm_api_config = self.config.get("llm_api", {})

            # Проверка наличия источников
            if not self.news_sources:
                logger.warning("В конфигурации нет источников новостей!")

            # Инициализация компонентов с проверкой
            self.news_parser = NewsParser(self.news_sources)
            self.news_analyzer = NewsAnalyzer(self.llm_api_config)
            self.dialog_manager = DialogManager(self.news_analyzer)
            self.dialog_interface = DialogInterface(self.dialog_manager)

            logger.info(f"Система инициализирована с {len(self.news_sources)} источниками")

        except Exception as e:
            logger.critical(f"Ошибка инициализации: {e}")
            sys.exit(1)

    def _load_config(self, config_path):
        """
        Улучшенная загрузка конфигурации с резервным копированием
        """
        default_config = {
            "news_sources": [
                {"name": "RBC", "url": "https://www.rbc.ru/economics/", "type": "rbc"},
                {"name": "РИА", "url": "https://sn.ria.ru", "type": "ria"}
            ],
            "llm_api": {
                "base_url": "https://api.llm7.io/v1",
                "api_key": "unused",
                "model": "gpt-4.1-nano"
            }
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                    # Проверка обязательных полей
                    if "news_sources" not in config or "llm_api" not in config:
                        logger.warning("В конфиге отсутствуют обязательные поля. Использую значения по умолчанию")
                        return default_config
                    return config
            else:
                logger.info("Файл конфигурации не найден. Создаю новый...")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                return default_config

        except json.JSONDecodeError:
            logger.error("Ошибка чтения конфига (неверный формат). Использую значения по умолчанию")
            return default_config
        except Exception as e:
            logger.error(f"Ошибка загрузки конфига: {e}. Использую значения по умолчанию")
            return default_config

    def start(self):
        """
        Улучшенный запуск системы с обработкой состояния
        """
        try:
            logger.info("=== Запуск системы ===")

            # Автоматическое обновление новостей при старте
            try:
                logger.info("Загрузка новостей...")
                news_count = len(self.news_parser.update_news())
                logger.info(f"Загружено {news_count} новостей")
            except Exception as e:
                logger.error(f"Ошибка при загрузке новостей: {e}")
                # Продолжаем работу, даже если новости не загрузились

            # Запуск интерфейса
            self.dialog_interface.run(self.news_parser)

        except KeyboardInterrupt:
            logger.info("Работа прервана пользователем")
        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}")
        finally:
            logger.info("=== Работа системы завершена ===")
            # Можно добавить сохранение состояния при выходе


if __name__ == "__main__":
    try:
        # Инициализация с явным указанием пути к конфигу
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        bot = EconomicNewsBot(config_path)
        bot.start()
    except Exception as e:
        logger.critical(f"Ошибка при запуске: {e}")
        sys.exit(1)