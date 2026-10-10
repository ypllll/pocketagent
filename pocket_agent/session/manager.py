"""把会话历史存进SQLite，让agent记住上下文，使得会话持久化"""

import sqlite3
from datetime import datetime
from pathlib import Path
from pocket_agent.models import Message

def __init__(self, db_path: str):
    self.db_path = db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)