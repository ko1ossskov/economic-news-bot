#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль парсинга экономических новостей
"""

import os
import json
import logging
import hashlib
import requests
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsParser:
    """
    Класс для парсинга экономических новостей из различных источников
    """
    
    def __init__(self, news_sources, cache_dir="cache"):
        """
        Инициализация парсера новостей
        
        Args:
            news_sources (list): Список источников новостей
            cache_dir (str): Директория для кэширования новостей
        """
        self.news_sources = news_sources
        self.cache_dir = cache_dir
        self.news_cache = {}
        
        # Создаем директорию для кэша, если она не существует
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Загружаем кэш новостей, если он существует
        cache_file = os.path.join(cache_dir, "news_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.news_cache = json.load(f)
                logger.info(f"Загружен кэш новостей: {len(self.news_cache)} записей")
            except Exception as e:
                logger.error(f"Ошибка загрузки кэша новостей: {e}")
        
        logger.info(f"Инициализирован парсер новостей с {len(news_sources)} источниками")

    def update_news(self):
        """
        Обновление списка новостей (исправленная версия)
        """
        try:
            all_news = []

            # Исправлено: используем self.news_sources вместо self.sources
            for source in self.news_sources:
                name = source.get("name", "")
                url = source.get("url", "")
                logger.info(f"Обновление новостей из {name}")

                if "rbc" in name.lower():
                    all_news.extend(self._parse_rbc(url, name))
                elif "ria" in name.lower():
                    all_news.extend(self._parse_ria(url, name))
                else:
                    logger.warning(f"Источник {name} не поддерживается")

            # Сохраняем в кэш
            self.news_cache = {news["id"]: news for news in all_news}
            self._save_cache()

            logger.info(f"Успешно обновлено: {len(all_news)} новостей")
            return all_news

        except Exception as e:
            logger.error(f"Ошибка при обновлении новостей: {e}")
            return []

    def get_latest_news(self, limit=5):
        """
        Получение последних новостей с проверкой типа limit

        Args:
            limit (int|None): Максимальное количество новостей
        """
        if not isinstance(limit, (int, type(None))):
            limit = 5  # Значение по умолчанию при неверном формате

        sorted_news = sorted(
            self.news_cache.values(),
            key=lambda x: x.get("date", ""),
            reverse=True
        )

        return sorted_news[:limit] if limit else sorted_news
    
    def search_news(self, query, limit=10):
        """
        Поиск новостей по ключевому слову
        
        Args:
            query (str): Поисковый запрос
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список найденных новостей
        """
        query = query.lower()
        results = []
        
        for news in self.news_cache.values():
            title = news.get("title", "").lower()
            content = news.get("content", "").lower()
            
            if query in title or query in content:
                results.append(news)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def _parse_rbc(self, url, source_name):
        """
        Парсинг новостей с сайта РБК
        
        Args:
            url (str): URL источника
            source_name (str): Название источника
            
        Returns:
            list: Список новостей
        """
        news_list = []
        
        try:
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим блоки с новостями
            news_blocks = soup.select('.news-feed__item')
            
            for block in news_blocks:
                try:
                    # Извлекаем заголовок
                    title_elem = block.select_one('.news-feed__item__title')
                    title = title_elem.text.strip() if title_elem else "Без заголовка"
                    
                    # Извлекаем ссылку
                    link_elem = block.select_one('a')
                    link = link_elem.get('href', '') if link_elem else ""
                    
                    # Извлекаем дату
                    date_elem = block.select_one('.news-feed__item__date')
                    date = date_elem.text.strip() if date_elem else ""
                    
                    # Генерируем уникальный ID
                    news_id = f"{source_name}_{self._generate_id(link)}"
                    
                    # Создаем объект новости
                    news_item = {
                        "id": news_id,
                        "title": title,
                        "url": link,
                        "date": date,
                        "source": source_name,
                        "content": ""  # Контент можно получить при переходе по ссылке
                    }
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге блока новости РБК: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге РБК: {e}")
        
        return news_list
    
    def _parse_ria(self, url, source_name):
        """
        Парсинг новостей с сайта РИА Новости
        
        Args:
            url (str): URL источника
            source_name (str): Название источника
            
        Returns:
            list: Список новостей
        """
        news_list = []
        
        try:
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим блоки с новостями
            news_blocks = soup.select('.list-item')
            
            for block in news_blocks:
                try:
                    # Извлекаем заголовок
                    title_elem = block.select_one('.list-item__title')
                    title = title_elem.text.strip() if title_elem else "Без заголовка"
                    
                    # Извлекаем ссылку
                    link_elem = block.select_one('a')
                    link = link_elem.get('href', '') if link_elem else ""
                    
                    # Если ссылка относительная, добавляем домен
                    if link and not link.startswith('http'):
                        link = f"https://sn.ria.ru{link}"
                    
                    # Извлекаем дату
                    date_elem = block.select_one('.list-item__date')
                    date = date_elem.text.strip() if date_elem else ""
                    
                    # Генерируем уникальный ID на основе ссылки
                    news_id = f"{source_name}_{self._generate_id(link)}"
                    
                    # Создаем объект новости
                    news_item = {
                        "id": news_id,
                        "title": title,
                        "url": link,
                        "date": date,
                        "source": source_name,
                        "content": ""  # Контент можно получить при переходе по ссылке
                    }
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    logger.error(f"Ошибка при парсинге блока новости РИА: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге РИА: {e}")
        
        return news_list



    def _generate_id(self, text):
        """
        Генерация уникального ID на основе текста
        
        Args:
            text (str): Исходный текст
            
        Returns:
            str: Уникальный ID
        """
        if not text:
            return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:10]
        
        # Извлекаем последнюю часть URL (обычно это уникальный идентификатор)
        parts = text.split('/')
        if parts:
            return parts[-1]
        
        return hashlib.md5(text.encode()).hexdigest()[:10]
    
    def _save_cache(self):
        """
        Сохранение кэша новостей
        """
        try:
            cache_file = os.path.join(self.cache_dir, "news_cache.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.news_cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранен кэш новостей: {len(self.news_cache)} записей")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша новостей: {e}")
