import json
from pathlib import Path
from typing import Optional, Any
from .models import StudentProfile, ConversationEntry


class MemoryManager:
    """Управление in-memory историей и persistent профилем"""

    def __init__(self, profile_path: str = "data/student_profile.json"):
        self.profile_path = Path(profile_path)
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

        self.conversation_history: list[ConversationEntry] = []
        self.profile = self.load_profile()

    def load_profile(self) -> StudentProfile:
        """Загрузить профиль из файла"""
        if self.profile_path.exists():
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StudentProfile(**data)
        return StudentProfile()

    def save_profile(self):
        """Сохранить профиль в файл"""
        with open(self.profile_path, 'w', encoding='utf-8') as f:
            json.dump(self.profile.model_dump(), f, indent=2, ensure_ascii=False)

    def add_message(self, role: str, content: str, agent: Optional[str] = None):
        """Добавить сообщение в историю"""
        from datetime import datetime
        entry = ConversationEntry(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            agent=agent
        )
        self.conversation_history.append(entry)

    def get_recent_history(self, limit: int = 10) -> list[ConversationEntry]:
        """Получить последние N сообщений"""
        return self.conversation_history[-limit:]

    def add_studied_topic(self, topic: str):
        """Отметить тему как изученную"""
        if topic not in self.profile.studied_topics:
            self.profile.studied_topics.append(topic)
            self.save_profile()

    def update_progress(self, key: str, value: Any):
        """Обновить заметку о прогрессе"""
        self.profile.progress_notes[key] = value
        self.save_profile()

    def clear_history(self):
        """Очистить историю текущей сессии"""
        self.conversation_history.clear()
