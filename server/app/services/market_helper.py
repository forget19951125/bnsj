"""
行情辅助：按交易对获取当前 1 分钟 K 开盘价与当前价（仅 ETHUSDT / BTCUSDT）
"""
import ccxt
import os
from typing import Optional, Tuple

# 允许的交易对 -> ccxt 合约 symbol
SYMBOL_MAP = {
    "ETHUSDT": "ETH/USDT:USDT",
    "BTCUSDT": "BTC/USDT:USDT",
}


def _get_exchange():
    """与 price_monitor 一致的币安合约 ccxt 实例"""
    config = {
        "rateLimit": 1200,
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    }
    proxy = os.getenv("BINANCE_PROXY")
    if proxy:
        config["proxies"] = {"http": proxy, "https": proxy}
    return ccxt.binance(config)


def get_current_candle_open_and_price(symbol_raw: str) -> Optional[Tuple[float, float]]:
    """
    获取「当前这一分钟正在走的 K 线」的开盘价，以及当前价格。
    symbol_raw: ETHUSDT 或 BTCUSDT
    返回: (当前分钟K开盘价, 当前价)，失败返回 None
    """
    symbol_raw = (symbol_raw or "").strip().upper()
    if symbol_raw not in SYMBOL_MAP:
        return None
    ccxt_symbol = SYMBOL_MAP[symbol_raw]
    try:
        exchange = _get_exchange()
        # 当前这根 1 分钟 K（未收盘）
        ohlcv = exchange.fetch_ohlcv(ccxt_symbol, "1m", limit=1)
        if not ohlcv:
            return None
        candle = ohlcv[0]
        open_price = float(candle[1])
        # 当前价用 ticker 更实时
        ticker = exchange.fetch_ticker(ccxt_symbol)
        current_price = float(ticker.get("last", candle[4]))
        return (open_price, current_price)
    except Exception as e:
        print(f"[market_helper] {symbol_raw} 获取K线/价格失败: {e}")
        return None
