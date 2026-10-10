"""创建客服工单，把用户的问题记录下来交给人工处理"""
import sqlite3
from datetime import date,datetime
from .base import Tool
from pocket_agent.models import ToolResult

class create_ticket(Tool):
    name="create_ticket"
    description = (
        "为用户创建一条客服工单，转交人工处理。"
        "当用户需要退款、赔偿、投诉、或问题无法通过查询解决时使用；"
        "用户明确要求转人工时也要使用。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "issue": {
                "type": "string",
                "description": "问题描述。要写清楚用户遇到的具体情况，例如『订单 ORD-5678 超过退货期限，用户不认可，要求人工处理』",
            },
            "order_id": {
                "type": "string",
                "description": "相关订单号（如果有），格式类似 ORD-1234",
            },
            "priority": {
                "type": "string",
                "description": "优先级：normal（一般咨询）或 urgent（投诉、退款争议）",
            },
        },
        "required": ["issue"],
    }

    def __init__(self,db_path:str):
        self.path=db_path
        conn=sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id   TEXT UNIQUE NOT NULL,
                issue       TEXT NOT NULL,
                order_id    TEXT,
                priority    TEXT,
                status      TEXT,
                created_at  TEXT
            )
        """)
        conn.commit()
        conn.close()

    def next_ticket_id(self,conn)->str:
        num=f"TK-{datetime.now():%Y%m%d}-"
        n=conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE ticket_id LIKE ?",
            (num+"%",)
        ).fetchone()[0]
        return f"{num}{n+1:03d}"

    def execute(self,issue:str,order_id:str="",priority:str="normal"):
        if priority not in ("normal","urgent"):
            priority="normal"

        conn=sqlite3.connect(self.path)
        try:
            ticket_id = self.next_ticket_id(conn)
            conn.execute(
                "INSERT INTO tickets"
                " (ticket_id, issue, order_id, priority, status, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    ticket_id,
                    issue,
                    order_id,
                    priority,
                    "open",
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return ToolResult(
            content=(
                f"工单已创建成功。\n"
                f"工单号：{ticket_id}\n"
                f"问题：{issue}\n"
                f"优先级：{'紧急' if priority == 'urgent' else '一般'}\n"
                f"状态：待处理\n"
                f"请把这个工单号告知用户，并说明人工客服会在 24 小时内联系。"
            )
        )