from typing import Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .models import (
    QueryClassification,
    TheoryResponse,
    CodeSolution,
    StudyPlan,
)


class RouterAgent:
    """Маршрутизатор запросов пользователя"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.system_prompt = """Ты агент-маршрутизатор в мультиагентной системе помощи студентам.

Твоя задача: проанализировать запрос пользователя и определить:
1. Тип запроса (theory / coding / planning / architecture)
2. Какие агенты должны быть задействованы
3. Уверенность в классификации (0-1)

Типы запросов:
- theory: вопросы про концепции, алгоритмы, теорию CS
- coding: помощь с кодом, реализацией, отладкой
- planning: создание планов обучения, разбивка задач
- architecture: проектирование систем, выбор технологий

Агенты:
- theory_agent: объясняет теорию
- code_helper_agent: помогает с кодом
- planner_agent: создаёт планы

Отвечай строго в JSON согласно схеме QueryClassification."""

    def classify(self, query: str) -> QueryClassification:
        """Классифицировать запрос пользователя"""
        response = self.llm.with_structured_output(QueryClassification).invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Запрос пользователя: {query}")
        ])
        return response


class TheoryAgent:
    """Агент для объяснения теории"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.system_prompt = """Ты эксперт по computer science и теории алгоритмов.

Твоя задача: объяснять концепции понятным языком с примерами.

При ответе укажи:
1. explanation: подробное объяснение концепции
2. key_concepts: список ключевых терминов
3. related_topics: связанные темы для изучения
4. difficulty_level: уровень сложности темы

Отвечай строго в JSON согласно схеме TheoryResponse."""

    def explain(self, topic: str, context: Optional[str] = None) -> TheoryResponse:
        """Объяснить теоретическую концепцию"""
        prompt = f"Объясни тему: {topic}"
        if context:
            prompt += f"\n\nКонтекст из истории диалога:\n{context}"

        response = self.llm.with_structured_output(TheoryResponse).invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ])
        return response


class CodeHelperAgent:
    """Агент для помощи с кодом"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.system_prompt = """Ты эксперт-программист, помогающий студентам с кодом.

Можешь:
- Генерировать код по описанию
- Объяснять готовый код
- Находить и исправлять ошибки
- Предлагать улучшения

При ответе укажи:
1. code: готовый код
2. language: язык программирования
3. explanation: объяснение решения
4. test_cases: примеры использования
5. complexity_analysis: анализ сложности (опционально)

Отвечай строго в JSON согласно схеме CodeSolution."""

    def generate_solution(self, task: str, language: str = "python") -> CodeSolution:
        """Сгенерировать решение задачи"""
        response = self.llm.with_structured_output(CodeSolution).invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Задача: {task}\nЯзык: {language}")
        ])
        return response


class PlannerAgent:
    """Агент для создания учебных планов"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.system_prompt = """Ты персональный планировщик обучения.

Твоя задача: создавать реалистичные учебные планы с учётом:
- Текущего уровня студента
- Доступного времени
- Целей обучения

При создании плана укажи:
1. title: название плана
2. goal: цель обучения
3. total_duration_days: общая длительность
4. tasks: список задач с датами и ресурсами
5. milestones: ключевые этапы

Отвечай строго в JSON согласно схеме StudyPlan."""

    def create_plan(self, goal: str, duration_days: int, level: str = "beginner") -> StudyPlan:
        """Создать учебный план"""
        response = self.llm.with_structured_output(StudyPlan).invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Цель: {goal}\nДлительность: {duration_days} дней\nУровень: {level}")
        ])
        return response
