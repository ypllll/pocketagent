"""写一个模拟查询订单的工具，当然数据是假的"""
from .base import Tool
from pocket_agent.models import ToolResult
from datetime import date

class query_order(Tool):
    name="query_order"
    description="根据订单号查询订单的商品、状态和签收日期。当用户询问自己的订单、要判断是否能退货/换货时需要先查订单"
    parameters={
        "type":"object",
        "properties":{
            "order_id":{
                "type":"string",
                "description":"这是订单号，格式类似ORD-1234"
            }
        },
        "required":["order_id"]
    }
    _FAKE_ORDERS = {
    # 签收 5 天前 → 在 7 天内 ✅ 可以退
    "ORD-1234": {"product": "iPhoneDuo Pro 512GB",
                 "signed_at": "2026-10-03", "status": "已签收"},

    # 签收 18 天前 → 超过 7 天，也超过 15 天换货 ❌
    "ORD-5678": {"product": "iPhoneDuo 标准版 256GB",
                 "signed_at": "2026-09-20", "status": "已签收"},

    # 签收 2 天前 → 时间上没问题，但【定制刻字】❌ 不支持无理由退货
    "ORD-9012": {"product": "iPhoneDuo Pro Max 1TB（定制刻字）",
                 "signed_at": "2026-10-06", "status": "已签收"},

    # 还没签收 → 不能走退货流程
    "ORD-3456": {"product": "iPhoneDuo 标准版 256GB",
                 "signed_at": None, "status": "运输中"},
}

    def execute(self, order_id:str)->ToolResult:
        order=self._FAKE_ORDERS.get(order_id)
        if not order:
            return ToolResult(
                content=f"未找到订单{order_id},请向用户确认订单号是否正确"
            )
        if order["status"]!="已签收":
            return ToolResult(
                content=f"订单{order_id}:{order['product']},状态：{order['status']},尚未签收"
            )
        signed=date.fromisoformat(order['signed_at'])
        days=(date.today()-signed).days
        return ToolResult(
            content=(
                f"订单{order_id}\n"
                f"商品{order['product']}\n"
                f"状态{order['status']}\n"
                f"签收日期：{order['signed_at']},距今{days}天"
            )
        )
        
        