import subprocess
import tempfile
import json
from typing import Any
from langchain_core.tools import tool


@tool
def search_notes(query: str) -> str:
    """
    Поиск информации в базе знаний студента.

    Args:
        query: поисковый запрос

    Returns:
        Релевантные фрагменты из базы знаний
    """
    try:
        from pathlib import Path
        kb_path = Path("data/knowledge_base.txt")

        if not kb_path.exists():
            return "База знаний пуста. Добавьте заметки в data/knowledge_base.txt"

        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Простой поиск по вхождению (можно заменить на semantic search)
        lines = content.split('\n')
        relevant = [line for line in lines if query.lower() in line.lower()]

        if not relevant:
            return f"Ничего не найдено по запросу '{query}'"

        return "\n".join(relevant[:5])  # Топ-5 результатов

    except Exception as e:
        return f"Ошибка поиска: {str(e)}"


@tool
def execute_code(code: str, language: str = "python") -> dict[str, Any]:
    """
    Выполняет код в изолированном окружении.

    Args:
        code: код для выполнения
        language: язык программирования (python, javascript и т.д.)

    Returns:
        dict с полями: success, output, error
    """
    if language != "python":
        return {
            "success": False,
            "output": "",
            "error": f"Язык {language} пока не поддерживается"
        }

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Превышено время выполнения (5 сек)"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


@tool
def save_plan(plan: dict) -> str:
    """
    Сохраняет учебный план в память.

    Args:
        plan: словарь с планом обучения

    Returns:
        Сообщение об успехе
    """
    try:
        from pathlib import Path
        plans_path = Path("data/study_plans.json")
        plans_path.parent.mkdir(parents=True, exist_ok=True)

        # Загрузить существующие планы
        if plans_path.exists():
            with open(plans_path, 'r', encoding='utf-8') as f:
                plans = json.load(f)
        else:
            plans = []

        # Добавить новый план
        plans.append(plan)

        # Сохранить
        with open(plans_path, 'w', encoding='utf-8') as f:
            json.dump(plans, f, indent=2, ensure_ascii=False)

        return f"План '{plan.get('title', 'Без названия')}' успешно сохранён"

    except Exception as e:
        return f"Ошибка сохранения плана: {str(e)}"


@tool
def get_history(limit: int = 10) -> list[dict]:
    """
    Получает историю диалога из текущей сессии.

    Args:
        limit: максимальное количество сообщений

    Returns:
        Список последних сообщений
    """
    # Этот инструмент будет использовать MemoryManager из state
    # Реализация в агенте, здесь заглушка
    return []
