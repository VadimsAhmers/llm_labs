from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


class QueryClassification(BaseModel):
    """Результат классификации запроса Router-агентом"""
    query_type: Literal["theory", "coding", "planning", "architecture"]
    reasoning: str
    target_agents: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class TheoryResponse(BaseModel):
    """Ответ Theory Agent"""
    explanation: str
    key_concepts: list[str]
    related_topics: list[str]
    difficulty_level: Literal["beginner", "intermediate", "advanced"]


class CodeSolution(BaseModel):
    """Решение от Code Helper Agent"""
    code: str
    language: str
    explanation: str
    test_cases: list[dict]
    complexity_analysis: Optional[str] = None


class StudyPlan(BaseModel):
    """План обучения от Planner Agent"""
    title: str
    goal: str
    total_duration_days: int
    tasks: list[dict]  # {day, task, resources}
    milestones: list[str]


class ConversationEntry(BaseModel):
    """Запись в истории диалога"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str
    agent: Optional[str] = None


class StudentProfile(BaseModel):
    """Профиль студента (долгосрочная память)"""
    studied_topics: list[str] = Field(default_factory=list)
    current_goals: list[str] = Field(default_factory=list)
    preferred_learning_style: Optional[str] = None
    progress_notes: dict[str, Any] = Field(default_factory=dict)