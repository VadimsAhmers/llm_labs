# Multi-Agent LeetCode Solver

Интеллектуальная система на базе LangGraph для автоматического решения задач с LeetCode с использованием нескольких подходов.

## Описание

Система использует паттерн ReAct (Reason-Act-Observe) для оркестрации процесса решения задач:

1. **Парсинг задачи** — автоматическое извлечение условия с веб-страницы LeetCode через HTTP-запросы и BeautifulSoup
2. **Планирование** — генерация 2-3 различных алгоритмических подходов (hash map, two pointers, DP и т.д.)
3. **Параллельная генерация** — одновременный вызов LLM для генерации кода всех подходов через `asyncio.gather()`
4. **Тестирование** — выполнение сгенерированных решений на извлеченных из условия тестах
5. **Анализ и сравнение** — LLM анализирует результаты тестирования, временную и пространственную сложность каждого подхода и выбирает оптимальное решение
6. **Итоговый отчет** — подробное сравнение всех подходов с результатами тестирования

## Ключевые возможности

- ✅ **ReAct Pattern** — LLM-управляемая логика принятия решений на каждом шаге
- ✅ **Structured Output** — типобезопасность через Pydantic модели (`LeetCodeTask`, `ApproachPlan`, `ApproachSolution`, `ComparisonAnalysis`)
- ✅ **Retry Logic** — автоматические повторы с экспоненциальной задержкой (через `tenacity`)
- ✅ **Async/Await** — асинхронные вызовы LLM для параллелизма
- ✅ **Универсальный парсер тестов** — динамическая обработка примеров из HTML-условия задачи
- ✅ **Изолированное выполнение** — запуск кода в отдельных процессах с таймаутом

## Установка

```bash
pip install langchain langgraph langchain-openai pydantic requests beautifulsoup4 python-dotenv nest-asyncio tenacity
```

## Конфигурация

Создайте файл `.env` в корне проекта:

```env
UNIVERSITY_API_BASE=https://your-api-endpoint.com/v1
UNIVERSITY_API_KEY=your-api-key
LLM_MODEL=qwen3-32b
REQUEST_TIMEOUT=10
CODE_EXECUTION_TIMEOUT=5
MAX_RETRIES=2
```

## Использование

### Запуск через ноутбук (рекомендуется)

Откройте `lab_1.ipynb` и выполните все ячейки. 



### Структура результата

```python
report.problem_title              # Название задачи
report.problem_difficulty         # Easy/Medium/Hard
report.all_solutions              # Список всех решений с результатами тестов
report.comparison                 # Сравнительный анализ с обоснованием
report.comparison.recommended_approach  # Рекомендуемый подход
```

## Архитектура

```
┌─────────────┐
│ ReAct Node  │  ← Анализирует state.next_step и маршрутизирует
└──────┬──────┘
       │
       ├─→ "parse_problem" ──→ ┌──────────────┐
       │                        │ Parser Node  │  ← Загружает условие (с retry через tenacity)
       │                        └──────────────┘
       │
       ├─→ "plan_approaches" ──→ ┌────────────────────┐
       │                          │ Multi-Planner Node │  ← Генерирует 2-3 подхода через LLM
       │                          └────────────────────┘
       │
       ├─→ "generate_solutions" ──→ ┌────────────────────────┐
       │                             │ Parallel Executor Node │  ← Генерирует и тестирует решения параллельно (asyncio.gather)
       │                             └────────────────────────┘
       │
       ├─→ "analyze_solutions" ──→ ┌───────────────┐
       │                            │ Analyzer Node │  ← Сравнивает решения через LLM
       │                            └───────────────┘
       │
       └─→ "finalize" ──→ ┌────────────────┐
                          │ Finalize Node  │  ← Создает MultiSolutionReport
                          └────────────────┘
```

## Система оценки решений

Финальная оценка решений происходит в `Analyzer Node` через LLM-анализ следующих критериев:

- **Успешность тестирования** — количество пройденных тестов
- **Временная сложность** — Big O нотация (извлекается из плана подхода)
- **Пространственная сложность** — использование дополнительной памяти
- **Сложность реализации** — читаемость и поддерживаемость кода

LLM выбирает оптимальный подход на основе взвешенного сравнения этих метрик и предоставляет обоснование в `ComparisonAnalysis.reasoning`.

## Примеры вывода

```
==== Problem summary ====
Title: Two Sum
Difficulty: Easy
Total approaches: 3
Successful approaches: 3
Recommended approach: hash_map

==== Approaches detail ====
Approach 1: hash_map
  Planned time complexity: O(n)
  Planned space complexity: O(n)
  Tests passed: 3/3
  Status: all tests passed

Approach 2: two_pointers
  Planned time complexity: O(n log n)
  Planned space complexity: O(1)
  Tests passed: 3/3
  Status: all tests passed
```

## Технические детали

### Технологии

- **LLM Provider**: `ChatOpenAI` с поддержкой пользовательских endpoints
- **Structured Output**: `PydanticOutputParser` для типобезопасного парсинга
- **Parallelism**: `asyncio.gather()` для параллельной генерации кода (LLM) и выполнения тестов всех подходов одновременно
- **Error Handling**: `tenacity` для retry с экспоненциальной задержкой
- **Code Execution**: `subprocess.run()` с изоляцией и таймаутами

### Pydantic модели

```python
LeetCodeTask         # Условие задачи с примерами
ApproachPlan         # План решения (название, сложности, шаги)
ApproachSolution     # Код решения с документацией
ExecutionResult      # Результаты тестирования
ComparisonAnalysis   # Сравнительный анализ с рекомендацией
MultiSolutionReport  # Финальный отчет со всеми данными
```

### Архитектура параллелизма

```python
# В parallel_executor_node():
solutions = await asyncio.gather(*[
    generate_solution_for_approach(approach, ...)  # Каждый подход обрабатывается параллельно
    for approach in state.planned_approaches
])

# Внутри generate_solution_for_approach():
results = await asyncio.gather(*[
    execute_code(...)  # Каждый тест выполняется параллельно
    for test in tests
])
```

## Требования

- Python 3.10+
- Доступ к LeetCode (для парсинга задач)
- OpenAI-совместимый API endpoint

## Лицензия

Учебный проект для курса по Advanced NLP and LLMs.
```