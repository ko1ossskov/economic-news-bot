#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль управления диалогом для системы анализа экономических новостей
"""

import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DialogManager:
    """
    Класс для управления диалогом и обработки запросов пользователя
    """
    
    def __init__(self, news_analyzer, context_size=5):
        """
        Инициализация менеджера диалога
        
        Args:
            news_analyzer (NewsAnalyzer): Анализатор новостей
            context_size (int): Размер контекста диалога (количество сохраняемых сообщений)
        """
        self.news_analyzer = news_analyzer
        self.context_size = context_size
        self.context = []
        
        logger.info("Инициализирован менеджер диалога")
    
    def add_to_context(self, message, role="user"):
        """
        Добавление сообщения в контекст диалога
        
        Args:
            message (str): Текст сообщения
            role (str): Роль отправителя (user/system)
        """
        self.context.append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Ограничиваем размер контекста
        if len(self.context) > self.context_size:
            self.context = self.context[-self.context_size:]
    
    def get_context(self):
        """
        Получение текущего контекста диалога
        
        Returns:
            list: Список сообщений в контексте
        """
        return self.context
    
    def clear_context(self):
        """
        Очистка контекста диалога
        """
        self.context = []
        logger.info("Контекст диалога очищен")

    def process_message(self, message, news_parser):
        """
        Обработка сообщения пользователя

        Args:
            message (str): Сообщение пользователя
            news_parser (NewsParser): Парсер новостей

        Returns:
            dict: Результат обработки сообщения
        """
        # Добавляем сообщение в контекст
        self.add_to_context(message)

        # Проверяем команду обновления новостей
        if message.lower() in ["обновить новости", "обновить", "update"]:
            try:
                news_parser.update_news()
                response = {"text": "Новости успешно обновлены!"}
            except Exception as e:
                logger.error(f"Ошибка при обновлении новостей: {e}")
                response = {"text": f"Произошла ошибка при обновлении новостей: {e}"}
        else:
            # Определяем намерение пользователя для остальных команд
            intent = self._determine_intent(message)

            # Обрабатываем сообщение в зависимости от намерения
            if intent == "get_latest_news":
                try:
                    if "все новости" in message.lower():
                        response = self._handle_latest_news(news_parser, limit=None)
                    elif "новости" in message.lower():
                        parts = message.lower().split()
                        if len(parts) > 1 and parts[1].isdigit():
                            response = self._handle_latest_news(news_parser, limit=int(parts[1]))
                        else:
                            response = self._handle_latest_news(news_parser)
                    else:
                        response = self._handle_latest_news(news_parser)
                except Exception as e:
                    logger.error(f"Ошибка обработки запроса новостей: {e}")
                    response = {
                        "text": "Произошла ошибка при обработке запроса",
                        "data": None,
                        "type": "error"
                    }
                # Обрабатываем варианты:
                if "все новости" in message.lower():
                    response = self._handle_latest_news(news_parser, limit=None)
                elif "новости" in message.lower():
                    # Пытаемся извлечь число, если указано (например "новости 10")
                    try:
                        limit = int(message.split()[-1])
                        response = self._handle_latest_news(news_parser, limit)
                    except (ValueError, IndexError):
                        response = self._handle_latest_news(news_parser)  # По умолчанию 5
                else:
                    response = self._handle_latest_news(news_parser)
            elif intent == "search_news":
                query = self._extract_search_query(message)
                response = self._handle_search_news(news_parser, query)
            elif intent == "analyze_news":
                response = self._handle_analyze_news(news_parser)
            elif intent == "get_summary":
                response = self._handle_get_summary(news_parser)
            elif intent == "help":
                response = self._handle_help()
            elif intent == "greeting":
                response = self._handle_greeting()
            else:
                response = self._handle_unknown()

        # Добавляем ответ в контекст
        self.add_to_context(response["text"], "system")

        return response

    def _determine_intent(self, message):
        """
        Улучшенное определение намерения пользователя

        Args:
            message (str): Сообщение пользователя

        Returns:
            str: Намерение пользователя
        """
        message = message.lower().strip()

        # Определяем приоритетные команды в первую очередь
        if "все новости" in message:
            return "get_all_news"  # Новый тип намерения для всех новостей

        if any(word in message for word in ["помощь", "помоги", "что ты умеешь", "команды"]):
            return "help"

        if any(word in message for word in ["привет", "здравствуй", "добрый день", "здравствуйте"]):
            return "greeting"

        # Команды с четкими ключевыми словами
        if any(word in message for word in ["найди", "поиск", "искать"]):
            return "search_news"

        if any(word in message for word in ["анализ", "проанализируй", "анализировать"]):
            return "analyze_news"

        if any(word in message for word in ["сводка", "резюме", "итоги", "сумма"]):
            return "get_summary"

        # Обработка запросов новостей с числовым параметром
        if ("новости" in message or "последние" in message) and any(word.isdigit() for word in message.split()):
            return "get_n_news"  # Новый тип намерения

        # Общие запросы новостей
        if any(word in message for word in ["новости", "последние"]):
            return "get_latest_news"

        # Определение по контексту
        if len(self.context) > 1:
            prev_message = self.context[-2]["content"].lower()
            if "новост" in prev_message:
                return "get_latest_news"

        # Намерение по умолчанию
        return "get_latest_news"
    
    def _extract_search_query(self, message):
        """
        Извлечение поискового запроса из сообщения
        
        Args:
            message (str): Сообщение пользователя
            
        Returns:
            str: Поисковый запрос
        """
        message = message.lower()
        
        # Простая система извлечения запроса
        for prefix in ["найди", "поиск", "искать", "найти"]:
            if prefix in message:
                parts = message.split(prefix, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Если не удалось извлечь запрос, возвращаем всё сообщение
        return message

    def _handle_latest_news(self, news_parser, limit=5):
        """
        Обработка запроса на получение новостей с защитой от ошибок

        Args:
            news_parser (NewsParser): Парсер новостей
            limit (int|None): Количество новостей (None - все)
        """
        try:
            # Защищаемся от нечисловых значений
            if isinstance(limit, str):
                if limit.isdigit():
                    limit = int(limit)
                else:
                    limit = None if limit.lower() == 'none' else 5

            latest_news = news_parser.get_latest_news(limit)

            if not latest_news:
                return {
                    "text": "Нет доступных новостей. Попробуйте обновить новости командой 'обновить новости'.",
                    "data": None,
                    "type": "latest_news"
                }

            text = f"Вот последние {len(latest_news)} новостей:\n\n"
            for i, news in enumerate(latest_news, 1):
                text += f"{i}. {news.get('title', 'Без заголовка')}\n"
                text += f"   Источник: {news.get('source', 'Неизвестно')}, Дата: {news.get('date', 'Нет даты')}\n\n"

            text += "Для анализа введите 'анализ новостей'"
            return {
                "text": text,
                "data": latest_news,
                "type": "latest_news"
            }

        except Exception as e:
            logger.error(f"Ошибка обработки новостей: {e}")
            return {
                "text": "Произошла ошибка при получении новостей",
                "data": None,
                "type": "error"
            }
    
    def _handle_search_news(self, news_parser, query, limit=5):
        """
        Обработка запроса на поиск новостей
        
        Args:
            news_parser (NewsParser): Парсер новостей
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            dict: Результат обработки запроса
        """
        # Выполняем поиск новостей
        search_results = news_parser.search_news(query, limit)
        
        if not search_results:
            return {
                "text": f"К сожалению, я не нашел новостей по запросу '{query}'. Попробуйте изменить запрос или получить последние новости командой 'последние новости'.",
                "data": None,
                "type": "search_news"
            }
        
        # Формируем текстовый ответ
        text = f"Результаты поиска по запросу '{query}':\n\n"
        
        for i, news in enumerate(search_results, 1):
            title = news.get("title", "Без заголовка")
            source = news.get("source", "Неизвестный источник")
            date = news.get("date", "Без даты")
            
            text += f"{i}. {title}\n"
            text += f"   Источник: {source}, Дата: {date}\n\n"
        
        text += "Для анализа этих новостей введите 'проанализировать новости'."
        
        return {
            "text": text,
            "data": search_results,
            "type": "search_news"
        }
    
    def _handle_analyze_news(self, news_parser, limit=3):
        """
        Обработка запроса на анализ новостей
        
        Args:
            news_parser (NewsParser): Парсер новостей
            limit (int): Максимальное количество новостей для анализа
            
        Returns:
            dict: Результат обработки запроса
        """
        # Получаем последние новости для анализа
        latest_news = news_parser.get_latest_news(limit)
        
        if not latest_news:
            return {
                "text": "К сожалению, у меня нет новостей для анализа. Попробуйте обновить новости командой 'обновить новости'.",
                "data": None,
                "type": "analyze_news"
            }
        
        # Анализируем каждую новость
        analysis_results = []
        for news in latest_news:
            analysis = self.news_analyzer.analyze_news(news)
            analysis_results.append({
                "news": news,
                "analysis": analysis
            })
        
        # Формируем текстовый ответ
        text = "Результаты анализа последних новостей:\n\n"
        
        for i, result in enumerate(analysis_results, 1):
            news = result["news"]
            analysis = result["analysis"]
            
            title = news.get("title", "Без заголовка")
            topic = analysis.get("topic", "Не определено")
            sentiment = analysis.get("sentiment", "neutral")
            key_points = analysis.get("key_points", ["Не определено"])
            impact = analysis.get("impact", "Не определено")
            
            # Преобразуем sentiment в русский текст
            sentiment_text = {
                "positive": "Позитивная",
                "negative": "Негативная",
                "neutral": "Нейтральная"
            }.get(sentiment, "Нейтральная")
            
            text += f"{i}. {title}\n"
            text += f"   Тема: {topic}\n"
            text += f"   Тональность: {sentiment_text}\n"
            text += f"   Ключевые моменты: {', '.join(key_points)}\n"
            text += f"   Потенциальное влияние: {impact}\n\n"
        
        text += "Для получения общей сводки введите 'сводка по новостям'."
        
        return {
            "text": text,
            "data": analysis_results,
            "type": "analyze_news"
        }
    
    def _handle_get_summary(self, news_parser, limit=5):
        """
        Обработка запроса на получение сводки по новостям
        
        Args:
            news_parser (NewsParser): Парсер новостей
            limit (int): Максимальное количество новостей для анализа
            
        Returns:
            dict: Результат обработки запроса
        """
        # Получаем последние новости для анализа
        latest_news = news_parser.get_latest_news(limit)
        
        if not latest_news:
            return {
                "text": "К сожалению, у меня нет новостей для создания сводки. Попробуйте обновить новости командой 'обновить новости'.",
                "data": None,
                "type": "get_summary"
            }
        
        # Создаем сводку по новостям
        summary = self.news_analyzer.summarize_news(latest_news)
        
        # Формируем текстовый ответ
        trends = summary.get("trends", ["Не определено"])
        overall_sentiment = summary.get("overall_sentiment", "neutral")
        key_events = summary.get("key_events", ["Не определено"])
        recommendations = summary.get("recommendations", ["Нет рекомендаций"])
        
        # Преобразуем overall_sentiment в русский текст
        sentiment_text = {
            "positive": "Позитивная",
            "negative": "Негативная",
            "neutral": "Нейтральная",
            "mixed": "Смешанная"
        }.get(overall_sentiment, "Нейтральная")
        
        text = "Сводка по последним экономическим новостям:\n\n"
        
        text += "Основные тренды и темы:\n"
        for trend in trends:
            text += f"- {trend}\n"
        
        text += f"\nОбщая тональность: {sentiment_text}\n\n"
        
        text += "Ключевые события и их влияние:\n"
        for event in key_events:
            text += f"- {event}\n"
        
        text += "\nРекомендации:\n"
        for recommendation in recommendations:
            text += f"- {recommendation}\n"
        
        return {
            "text": text,
            "data": summary,
            "type": "get_summary"
        }
    
    def _handle_help(self):
        """
        Обработка запроса на получение справки
        
        Returns:
            dict: Результат обработки запроса
        """
        text = """Я - диалоговая система для анализа экономических новостей. Вот что я умею:

        1. Показывать последние новости:
           - 'новости' - 5 последних новостей
           - 'все новости' - полный список
        2. Искать новости по ключевым словам: 'найди [запрос]'
        3. Анализировать новости: 'анализ новостей'
        4. Создавать сводку: 'сводка'
        5. Обновлять новости: 'обновить новости'"""

        return {
            "text": text,
            "data": None,
            "type": "help"
        }
    
    def _handle_greeting(self):
        """
        Обработка приветствия
        
        Returns:
            dict: Результат обработки запроса
        """
        text = """Здравствуйте! Я - диалоговая система для анализа экономических новостей.

Я могу показывать последние новости, искать новости по ключевым словам, анализировать их и создавать сводки.

Чем я могу вам помочь сегодня? Напишите 'помощь', чтобы узнать о моих возможностях."""
        
        return {
            "text": text,
            "data": None,
            "type": "greeting"
        }
    
    def _handle_unknown(self):
        """
        Обработка неизвестного запроса
        
        Returns:
            dict: Результат обработки запроса
        """
        text = """Извините, я не совсем понял ваш запрос. Вот что я умею:

1. Показывать последние новости - просто напишите 'новости' или 'последние новости'
2. Искать новости по ключевым словам - напишите 'найди [запрос]' или 'поиск [запрос]'
3. Анализировать новости - напишите 'анализ новостей' или 'проанализируй новости'
4. Создавать сводку по новостям - напишите 'сводка' или 'резюме новостей'

Попробуйте сформулировать запрос иначе или напишите 'помощь' для получения справки."""
        
        return {
            "text": text,
            "data": None,
            "type": "unknown"
        }
