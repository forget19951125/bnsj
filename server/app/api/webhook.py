"""
Webhook 接收 API（如 TradingView）
收到 POST 后将 body 转发到 TG 群；若为 TV 信号格式则解析并延迟 30 秒后按条件创建订单。
"""
import asyncio
import json
from typing import Optional, List, Tuple
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/webhook", tags=["Webhook"])

# Telegram 单条消息长度限制
TG_MAX_TEXT = 4000

# TV 信号白名单
ALLOWED_SYMBOLS = {"ETHUSDT", "BTCUSDT"}
ALLOWED_DIRECTIONS = {"多", "空"}
ALLOWED_PERIODS = {"10", "30"}

# 方向 -> 订单方向
DIRECTION_MAP = {"多": "LONG", "空": "SHORT"}
# 周期 -> time_increments
PERIOD_MAP = {"10": "TEN_MINUTE", "30": "THIRTY_MINUTE"}


def _parse_tv_signal(text: str) -> Optional[Tuple[str, str, str]]:
    """
    解析 TV 纯文本信号，格式: SYMBOL|方向|周期|...
    返回 (symbol, direction_cn, period_str) 或 None
    """
    if not text or "|" not in text:
        return None
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        return None
    symbol = (parts[0] or "").upper()
    direction_cn = parts[1]
    period_str = parts[2].strip()
    return (symbol, direction_cn, period_str)


def _send_to_telegram(text: str, extra_chat_ids: Optional[list] = None) -> bool:
    """同步发送到默认 TG 群，若有 extra_chat_ids 则同时发到这些群。"""
    from ..services.telegram_service import send_message
    if len(text) > TG_MAX_TEXT:
        text = text[:TG_MAX_TEXT] + "\n\n...(已截断)"
    ok = send_message(text)
    for cid in extra_chat_ids or []:
        cid = (cid or "").strip()
        if cid:
            send_message(text, chat_id=cid)
    return ok


async def _tv_signal_create_order(symbol: str, direction_cn: str, period_str: str) -> None:
    """
    延迟 30 秒后检查条件并创建订单（仅 ETHUSDT/BTCUSDT，多/空，10/30）。
    """
    await asyncio.sleep(30)
    from ..database import SessionLocal
    from ..services.market_helper import get_current_candle_open_and_price
    from ..services.order_service import OrderService

    db = SessionLocal()
    try:
        result = get_current_candle_open_and_price(symbol)
        if result is None:
            print(f"[TV] {symbol} 获取行情失败，跳过创建订单")
            return
        open_price, current_price = result

        direction = DIRECTION_MAP.get(direction_cn)
        time_increments = PERIOD_MAP.get(period_str)
        if not direction or not time_increments:
            print(f"[TV] 方向或周期无效: {direction_cn} {period_str}")
            return

        # 空：当前价 < 当前分钟K开盘价；多：当前价 > 当前分钟K开盘价
        if direction == "SHORT":
            if current_price >= open_price:
                print(f"[TV] 空单条件不满足: 当前价 {current_price} >= K开盘 {open_price}，跳过")
                return
        else:  # LONG
            if current_price <= open_price:
                print(f"[TV] 多单条件不满足: 当前价 {current_price} <= K开盘 {open_price}，跳过")
                return

        order = OrderService.create_order(
            db,
            time_increments=time_increments,
            symbol_name=symbol,
            direction=direction,
            valid_duration=5,
        )
        print(f"[TV] 已创建订单: id={order.id} {symbol} {direction} {time_increments} 有效期5秒")
    except Exception as e:
        print(f"[TV] 创建订单异常: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/tradingview")
async def tradingview_webhook(request: Request):
    """
    TradingView Webhook 接收端点。
    Body 原样转发到 TG；若为「SYMBOL|方向|周期|...」且符合白名单则延迟 30 秒后按条件创建订单。
    """
    body = b""
    try:
        body = await request.body()
        raw_text = (body.decode("utf-8", errors="replace") or "").strip()

        # 转发到 TG
        try:
            data = json.loads(body) if body else {}
            text = "📩 TradingView Webhook\n\n" + json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            text = "📩 TradingView Webhook (raw)\n\n" + (raw_text or "(empty)")
        from ..config import settings
        extra: List[str] = [s.strip() for s in (settings.tg_chat_id_webhook or "").split(",") if s.strip()]
        _send_to_telegram(text, extra_chat_ids=extra)

        # 解析 TV 信号并判断是否进入下单流程
        parsed = _parse_tv_signal(raw_text)
        if parsed:
            symbol, direction_cn, period_str = parsed
            if symbol in ALLOWED_SYMBOLS and direction_cn in ALLOWED_DIRECTIONS and period_str in ALLOWED_PERIODS:
                asyncio.create_task(_tv_signal_create_order(symbol, direction_cn, period_str))

        return JSONResponse(content={"ok": True, "message": "received"})
    except Exception as e:
        raw = body.decode("utf-8", errors="replace")[:500] if body else "(empty)"
        from ..config import settings
        extra = [s.strip() for s in (settings.tg_chat_id_webhook or "").split(",") if s.strip()]
        _send_to_telegram(f"📩 Webhook 处理异常: {e}\n\nbody: {raw}", extra_chat_ids=extra)
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=500)
