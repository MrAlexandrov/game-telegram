#!/usr/bin/env python3
"""
Скрипт запуска только админского бота
"""
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Устанавливаем режим
os.environ['MODE'] = 'admin'

if __name__ == "__main__":
    from src.main import run
    run()