"""
Webhook 接收 API（如 TradingView）
收到 POST 后将 body 以 JSON 形式转发到 TG 群
"""
import json
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])

# Telegram 单条消息长度限制
TG_MAX_TEXT = 4000


def _send_to_telegram(text: str, extra_chat_ids: Optional[list] = None) -> bool:
    """同步发送到默认 TG 群，若有 extra_chat_ids 则同时发到这些群。"""
    from ..services.telegram_service import send_message
    from ..config import settings
    if len(text) > TG_MAX_TEXT:
        text = text[:TG_MAX_TEXT] + "\n\n...(已截断)"
    ok = send_message(text)
    for cid in extra_chat_ids or []:
        cid = (cid or "").strip()
        if cid:
            send_message(text, chat_id=cid)
    return ok


@router.post("/tradingview")
async def tradingview_webhook(request: Request):
    """
    TradingView Webhook 接收端点。
    任意 JSON body 会原样转发到配置的 TG 群，便于分析格式。
    """
    body = b""
    try:
        body = await request.body()
        # 尝试解析为 JSON 再格式化输出，便于阅读
        try:
            data = json.loads(body) if body else {}
            text = "📩 TradingView Webhook\n\n" + json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            text = "📩 TradingView Webhook (raw)\n\n" + (body.decode("utf-8", errors="replace") or "(empty)")
        from ..config import settings
        extra = [s.strip() for s in (settings.tg_chat_id_webhook or "").split(",") if s.strip()]
        _send_to_telegram(text, extra_chat_ids=extra)
        return JSONResponse(content={"ok": True, "message": "received"})
    except Exception as e:
        raw = body.decode("utf-8", errors="replace")[:500] if body else "(empty)"
        from ..config import settings
        extra = [s.strip() for s in (settings.tg_chat_id_webhook or "").split(",") if s.strip()]
        _send_to_telegram(f"📩 Webhook 处理异常: {e}\n\nbody: {raw}", extra_chat_ids=extra)
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)
