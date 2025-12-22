from typing import Annotated, Optional, Literal
from typing_extensions import TypedDict
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .models import (
    QueryClassification,
    TheoryResponse,
    CodeSolution,
    StudyPlan,
    ConversationEntry,
)
from .agents import RouterAgent, TheoryAgent, CodeHelperAgent, PlannerAgent
from .memory import MemoryManager
from .tools import search_notes, execute_code, save_plan


class GraphState(TypedDict):
    """Состояние графа мультиагентной системы"""
    # Входные данные
    user_query: str
    query_type: Optional[Literal["theory", "coding", "planning", "architecture"]]

    # Контекст
    conversation_history: list[ConversationEntry]
    relevant_notes: list[str]

    # Результаты агентов
    classification: Optional[QueryClassification]
    theory_response: Optional[TheoryResponse]
    code_solution: Optional[CodeSolution]
    study_plan: Optional[StudyPlan]

    # Финальный ответ
    final_response: str

    # Служебные поля
    errors: Annotated[list[str], operator.add]
    current_agent: Optional[str]


class MultiAgentGraph:
    """Граф мультиагентной системы помощника по учёбе"""

    def __init__(self, llm: ChatOpenAI, memory: MemoryManager):
        self.llm = llm
        self.memory = memory

        # Инициализация агентов
        self.router = RouterAgent(llm)
        self.theory_agent = TheoryAgent(llm)
        self.code_helper = CodeHelperAgent(llm)
        self.planner = PlannerAgent(llm)

        # Построение графа
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Построить граф состояний"""
        workflow = StateGraph(GraphState)

        # Узлы
        workflow.add_node("router", self._router_node)
        workflow.add_node("theory", self._theory_node)
        workflow.add_node("coding", self._coding_node)
        workflow.add_node("planning", self._planning_node)
        workflow.add_node("finalize", self._finalize_node)

        # Точка входа
        workflow.set_entry_point("router")

        # Условные рёбра (handoff)
        workflow.add_conditional_edges(
            "router",
            self._route_query,
            {
                "theory": "theory",
                "coding": "coding",
                "planning": "planning",
                "architecture": "theory",  # архитектура → theory agent
            }
        )

        # Все агенты ведут к финализации
        workflow.add_edge("theory", "finalize")
        workflow.add_edge("coding", "finalize")
        workflow.add_edge("planning", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _router_node(self, state: GraphState) -> GraphState:
        """Узел маршрутизации запроса"""
        query = state["user_query"]

        # Получить контекст из памяти
        history = self.memory.get_recent_history(limit=5)
        context = "\n".join([f"{h.role}: {h.content}" for h in history])

        # Классифицировать запрос
        classification = self.router.classify(query)

        state["classification"] = classification
        state["query_type"] = classification.query_type
        state["current_agent"] = "router"

        print(f"[Router] Type: {classification.query_type}")
        print(f"[Router] Confidence: {classification.confidence:.2f}")
        print(f"[Router] Reasoning: {classification.reasoning}")

        return state

    def _route_query(self, state: GraphState) -> str:
        """Условная маршрутизация на основе классификации"""
        return state["query_type"]

    def _theory_node(self, state: GraphState) -> GraphState:
        """Узел обработки теоретических вопросов"""
        query = state["user_query"]

        # Поиск релевантных заметок
        notes_result = search_notes.invoke({"query": query})
        state["relevant_notes"] = [notes_result]

        # Получить объяснение
        context = "\n".join(state["relevant_notes"])
        response = self.theory_agent.explain(topic=query, context=context)

        state["theory_response"] = response
        state["current_agent"] = "theory_agent"

        # Обновить профиль
        for concept in response.key_concepts:
            self.memory.add_studied_topic(concept)

        print(f"[Theory Agent] Explained: {query}")
        print(f"[Theory Agent] Level: {response.difficulty_level}")

        return state

    def _coding_node(self, state: GraphState) -> GraphState:
        """Узел помощи с кодом"""
        query = state["user_query"]

        # Генерация решения
        solution = self.code_helper.generate_solution(task=query, language="python")

        # Выполнение кода (если есть тесты)
        if solution.test_cases:
            exec_result = execute_code.invoke({
                "code": solution.code,
                "language": solution.language,
            })
            print(f"[Code Helper] Execution: {exec_result}")

        state["code_solution"] = solution
        state["current_agent"] = "code_helper_agent"

        print(f"[Code Helper] Generated solution in {solution.language}")

        return state

    def _planning_node(self, state: GraphState) -> GraphState:
        """Узел создания учебных планов"""
        query = state["user_query"]

        # Извлечь параметры из запроса (упрощённо)
        duration = 30  # по умолчанию 30 дней
        level = "beginner"

        # Создать план
        plan = self.planner.create_plan(
            goal=query,
            duration_days=duration,
            level=level
        )

        # Сохранить план
        save_result = save_plan.invoke({"plan": plan.model_dump()})
        print(f"[Planner] {save_result}")

        state["study_plan"] = plan
        state["current_agent"] = "planner_agent"

        print(f"[Planner] Created plan: {plan.title}")
        print(f"[Planner] Duration: {plan.total_duration_days} days")

        return state

    def _finalize_node(self, state: GraphState) -> GraphState:
        """Узел финализации и формирования ответа"""
        query_type = state["query_type"]

        # Формирование финального ответа
        if query_type == "theory":
            response = state["theory_response"]
            final = f"""**Объяснение:**
{response.explanation}

**Ключевые концепции:**
{', '.join(response.key_concepts)}

**Связанные темы:**
{', '.join(response.related_topics)}

**Уровень сложности:** {response.difficulty_level}
"""

        elif query_type == "coding":
            solution = state["code_solution"]
            final = f"""**Решение:**

```{solution.language}
{solution.code}
Объяснение: {solution.explanation}
Тестовые примеры: {chr(10).join(f"- {tc}" for tc in solution.test_cases)} """
        elif query_type == "planning":
            plan = state["study_plan"]
            tasks_str = "\n".join([
                f"{i+1}. {task}"
                for i, task in enumerate(plan.tasks)
            ])
            final = f"""**План обучения: {plan.title}**
Цель: {plan.goal}
Длительность: {plan.total_duration_days} дней
Задачи: {tasks_str}
Ключевые этапы: {chr(10).join(f"- {m}" for m in plan.milestones)} """
        else:
            final = "Извините, не удалось обработать запрос."

        state["final_response"] = final

        # Сохранить в память
        self.memory.add_message("user", state["user_query"])
        self.memory.add_message(
            "assistant",
            final,
            agent=state["current_agent"]
        )

        return state

    def invoke(self, query: str) -> str:
        """Запустить граф для обработки запроса"""
        initial_state: GraphState = {
            "user_query": query,
            "query_type": None,
            "conversation_history": self.memory.get_recent_history(),
            "relevant_notes": [],
            "classification": None,
            "theory_response": None,
            "code_solution": None,
            "study_plan": None,
            "final_response": "",
            "errors": [],
            "current_agent": None,
        }

        final_state = self.app.invoke(initial_state)
        return final_state["final_response"]