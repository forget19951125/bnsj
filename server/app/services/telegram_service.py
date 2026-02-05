"""
Telegram 推送服务
通过 Bot API 向指定群/用户发送消息
"""
import httpx
from typing import Optional
from ..config import settings


def send_message(text: str, chat_id: Optional[str] = None) -> bool:
    """
    发送一条文本到指定或配置的 TG 群/用户。
    chat_id 为 None 时使用 settings.tg_chat_id。
    若未配置 TG_BOT_TOKEN 或无有效 chat_id，直接返回 False 不报错。
    """
    token = (settings.tg_bot_token or "").strip()
    cid = (chat_id or settings.tg_chat_id or "").strip()
    if not token or not cid:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": cid, "text": text, "disable_web_page_preview": True}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, json=payload)
            if r.is_success:
                return True
            print(f"[TG] 发送失败: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"[TG] 发送异常: {e}")
        return False


async def send_message_async(text: str) -> bool:
    """异步发送（用于 startup 等异步上下文）"""
    import sys
    token = (settings.tg_bot_token or "").strip()
    chat_id = (settings.tg_chat_id or "").strip()
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload)
            if r.is_success:
                return True
            err = f"[TG] 发送失败: {r.status_code} {r.text}"
            sys.stderr.write(err + "\n")
            sys.stderr.flush()
            return False
    except Exception as e:
        err = f"[TG] 发送异常: {e}"
        sys.stderr.write(err + "\n")
        sys.stderr.flush()
        return False
