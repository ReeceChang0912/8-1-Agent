from family_agent.chat_history import ChatHistoryManager


class FakeChatDb:
    def __init__(self):
        self.calls = []

    def create_chat_session(self, user_id, title=None, family_id=""):
        self.calls.append(("create", user_id, title, family_id))
        return {"session_id": "s1", "family_id": family_id, "user_id": user_id, "title": title or "new"}

    def list_chat_sessions(self, user_id, limit=50, family_id=""):
        self.calls.append(("list", user_id, limit, family_id))
        return []

    def update_chat_session_title(self, user_id, session_id, title, family_id=""):
        self.calls.append(("update", user_id, session_id, title, family_id))
        return True

    def archive_chat_session(self, user_id, session_id, family_id=""):
        self.calls.append(("archive", user_id, session_id, family_id))
        return True

    def add_chat_message(self, user_id, role, content, emotion=None, session_id=None, family_id=""):
        self.calls.append(("add", user_id, role, content, emotion, session_id, family_id))

    def get_chat_history(self, user_id, limit=50, session_id=None, family_id=""):
        self.calls.append(("history", user_id, limit, session_id, family_id))
        return []

    def clear_chat_history(self, user_id, session_id=None, family_id=""):
        self.calls.append(("clear", user_id, session_id, family_id))


def test_chat_history_passes_family_boundary_to_database():
    db = FakeChatDb()
    manager = ChatHistoryManager(db_manager=db)

    manager.create_session("mom", "dinner", family_id="family-a")
    manager.list_sessions("mom", family_id="family-a")
    manager.update_session_title("mom", "s1", "new title", family_id="family-a")
    manager.archive_session("mom", "s1", family_id="family-a")
    manager.add_message("mom", "user", "hello", session_id="s1", family_id="family-a")
    manager.get_history("mom", session_id="s1", family_id="family-a")
    manager.clear_history("mom", session_id="s1", family_id="family-a")

    assert all(call[-1] == "family-a" for call in db.calls)
