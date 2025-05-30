#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль анализа экономических новостей с использованием языковой модели
"""

import os
import json
import logging
from datetime import datetime
import openai

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """
    Класс для анализа экономических новостей с использованием языковой модели
    """
    
    def __init__(self, llm_api_config, cache_dir="cache"):
        """
        Инициализация анализатора новостей
        
        Args:
            llm_api_config (dict): Конфигурация API языковой модели
            cache_dir (str): Директория для кэширования результатов анализа
        """
        self.llm_api_config = llm_api_config
        self.cache_dir = cache_dir
        self.analysis_cache = {}
        
        # Создаем директорию для кэша, если она не существует
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Загружаем кэш анализа, если он существует
        cache_file = os.path.join(cache_dir, "analysis_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.analysis_cache = json.load(f)
                logger.info(f"Загружен кэш анализа: {len(self.analysis_cache)} записей")
            except Exception as e:
                logger.error(f"Ошибка загрузки кэша анализа: {e}")
        
        # Инициализируем клиент OpenAI
        self.client = openai.OpenAI(
            base_url=llm_api_config.get("base_url", "https://api.llm7.io/v1"),
            api_key=llm_api_config.get("api_key", "unused")
        )
        
        self.model = llm_api_config.get("model", "gpt-4.1-nano")
        
        logger.info(f"Инициализирован анализатор новостей с моделью {self.model}")
    
    def analyze_news(self, news_item):
        """
        Анализ отдельной новости
        
        Args:
            news_item (dict): Новость для анализа
            
        Returns:
            dict: Результат анализа
        """
        # Проверяем, есть ли анализ в кэше
        news_id = news_item.get("id")
        if news_id and news_id in self.analysis_cache:
            logger.info(f"Найден кэшированный анализ для новости {news_id}")
            return self.analysis_cache[news_id]
        
        # Формируем запрос к языковой модели
        title = news_item.get("title", "")
        source = news_item.get("source", "")
        date = news_item.get("date", "")
        url = news_item.get("url", "")
        
        prompt = f"""Проанализируй экономическую новость и предоставь структурированный анализ в формате JSON:

Новость: {title}
Источник: {source}
Дата: {date}
URL: {url}

Требуемый формат ответа:
{{
  "topic": "основная тема новости (например, монетарная политика, фондовый рынок, инфляция и т.д.)",
  "sentiment": "тональность новости (positive/negative/neutral)",
  "key_points": ["ключевой момент 1", "ключевой момент 2", "ключевой момент 3"],
  "impact": "потенциальное влияние на экономику и рынки"
}}

Ответ должен быть только в формате JSON без дополнительного текста."""
        
        try:
            # Отправляем запрос к языковой модели
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - аналитик экономических новостей."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Получаем ответ модели
            result_text = response.choices[0].message.content
            
            # Извлекаем JSON из ответа
            result_json = self._extract_json(result_text)
            
            # Сохраняем результат в кэш
            if news_id:
                self.analysis_cache[news_id] = result_json
                self._save_cache()
            
            logger.info(f"Выполнен анализ новости {news_id}")
            return result_json
            
        except Exception as e:
            logger.error(f"Ошибка при анализе новости: {e}")
            
            # Возвращаем заглушку в случае ошибки
            return {
                "topic": "не удалось определить",
                "sentiment": "neutral",
                "key_points": ["Не удалось проанализировать новость"],
                "impact": "Не удалось определить влияние"
            }
    
    def analyze_news_batch(self, news_items):
        """
        Анализ группы новостей
        
        Args:
            news_items (list): Список новостей для анализа
            
        Returns:
            list: Результаты анализа
        """
        results = []
        
        for news in news_items:
            analysis = self.analyze_news(news)
            results.append({
                "news": news,
                "analysis": analysis
            })
        
        return results
    
    def summarize_news(self, news_items):
        """
        Создание сводки по группе новостей
        
        Args:
            news_items (list): Список новостей для анализа
            
        Returns:
            dict: Сводка по новостям
        """
        # Сначала анализируем каждую новость
        analysis_results = []
        for news in news_items:
            analysis = self.analyze_news(news)
            analysis_results.append({
                "title": news.get("title", ""),
                "analysis": analysis
            })
        
        # Формируем запрос к языковой модели для создания сводки
        prompt = "Создай сводку по следующим экономическим новостям и их анализу:\n\n"
        
        for i, result in enumerate(analysis_results, 1):
            title = result["title"]
            analysis = result["analysis"]
            
            prompt += f"Новость {i}: {title}\n"
            prompt += f"Тема: {analysis.get('topic', 'Не определено')}\n"
            prompt += f"Тональность: {analysis.get('sentiment', 'neutral')}\n"
            prompt += f"Ключевые моменты: {', '.join(analysis.get('key_points', ['Не определено']))}\n"
            prompt += f"Влияние: {analysis.get('impact', 'Не определено')}\n\n"
        
        prompt += """Предоставь сводку в формате JSON:
{
  "trends": ["тренд 1", "тренд 2", "тренд 3"],
  "overall_sentiment": "общая тональность (positive/negative/neutral/mixed)",
  "key_events": [{"event": "ключевое событие 1", "impact": "влияние события 1"}, {"event": "ключевое событие 2", "impact": "влияние события 2"}],
  "recommendations": "рекомендации для инвесторов и бизнеса"
}

Ответ должен быть только в формате JSON без дополнительного текста."""
        
        try:
            # Отправляем запрос к языковой модели
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - аналитик экономических новостей."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Получаем ответ модели
            result_text = response.choices[0].message.content
            
            # Извлекаем JSON из ответа
            result_json = self._extract_json(result_text)
            
            logger.info(f"Создана сводка по {len(news_items)} новостям")
            return result_json
            
        except Exception as e:
            logger.error(f"Ошибка при создании сводки: {e}")
            
            # Возвращаем заглушку в случае ошибки
            return {
                "trends": ["Не удалось определить тренды"],
                "overall_sentiment": "neutral",
                "key_events": [{"event": "Не удалось определить ключевые события", "impact": "Не удалось определить влияние"}],
                "recommendations": "Не удалось сформировать рекомендации"
            }
    
    def _extract_json(self, text):
        """
        Извлечение JSON из текста
        
        Args:
            text (str): Текст, содержащий JSON
            
        Returns:
            dict: Извлеченный JSON
        """
        try:
            # Пытаемся найти JSON в тексте
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            
            # Если не удалось найти JSON, пробуем загрузить весь текст
            return json.loads(text)
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении JSON: {e}")
            return {}
    
    def _save_cache(self):
        """
        Сохранение кэша анализа
        """
        try:
            cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранен кэш анализа: {len(self.analysis_cache)} записей")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша анализа: {e}")
