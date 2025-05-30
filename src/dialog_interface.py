#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Консольный интерфейс для диалоговой системы анализа экономических новостей
"""

import logging
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

logger = logging.getLogger(__name__)

class DialogInterface:
    """
    Класс для консольного интерфейса диалоговой системы
    """
    
    def __init__(self, dialog_manager):
        """
        Инициализация консольного интерфейса
        
        Args:
            dialog_manager (DialogManager): Менеджер диалога
        """
        self.dialog_manager = dialog_manager
        self.console = Console()
        self.running = False
        
        logger.info("Инициализирован консольный интерфейс")
    
    def display_welcome(self):
        """
        Отображение приветственного сообщения
        """
        self.console.print("\n")
        welcome_text = Text("Диалоговая система для анализа экономических новостей", style="bold green")
        self.console.print(Panel(welcome_text, expand=False))
        self.console.print("\nВведите 'помощь' для получения списка команд или 'выход' для завершения работы.\n")
    
    def display_message(self, message, message_type="system"):
        """
        Отображение сообщения в консоли
        
        Args:
            message (str): Текст сообщения
            message_type (str): Тип сообщения (system/user)
        """
        if message_type == "user":
            prefix = Text("Вы: ", style="bold blue")
            message_text = Text(message)
            self.console.print(prefix + message_text)
        else:
            prefix = Text("Система: ", style="bold green")
            message_text = Text(message)
            self.console.print(Panel(message_text, expand=False, border_style="green"))
        
        self.console.print("\n")
    
    def get_user_input(self):
        """
        Получение ввода пользователя
        
        Returns:
            str: Текст введенный пользователем
        """
        try:
            user_input = Prompt.ask("[bold blue]Вы[/bold blue]")
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            return "выход"

    def run(self, news_parser):
        """
        Запуск консольного интерфейса с улучшенной обработкой ошибок
        """
        self.running = True
        self.display_welcome()

        try:
            # Приветственное сообщение с обработкой ошибок
            try:
                greeting_response = self.dialog_manager._handle_greeting()
                self.display_message(greeting_response["text"])
            except Exception as e:
                logger.error(f"Ошибка приветствия: {e}")
                self.display_message("Добро пожаловать в систему анализа новостей!")

            while self.running:
                try:
                    user_input = self.get_user_input()

                    # Нормализация и проверка команды выхода
                    if user_input.strip().lower() in {"выход", "exit", "quit", "q"}:
                        self.console.print("[bold yellow]Завершение работы...[/bold yellow]")
                        break

                    # Пропуск пустых команд
                    if not user_input.strip():
                        continue

                    # Отображение и обработка ввода
                    self.display_message(user_input, "user")
                    response = self.dialog_manager.process_message(user_input, news_parser)
                    self.display_message(response["text"])

                    # Оптимизированная задержка
                    time.sleep(0.3)

                except KeyboardInterrupt:
                    self.console.print("\n[bold yellow]Для выхода введите 'выход'[/bold yellow]")
                    continue

                except Exception as e:
                    logger.error(f"Ошибка обработки команды '{user_input}': {e}")
                    self.display_message("Ошибка выполнения команды. Попробуйте снова.")

        except Exception as e:
            logger.critical(f"Критическая ошибка: {e}")
            self.console.print("[bold red]Произошла критическая ошибка[/bold red]")

        finally:
            self.console.print("[bold green]Спасибо за использование системы![/bold green]")
            self.running = False