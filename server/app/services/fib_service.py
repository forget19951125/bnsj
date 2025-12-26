"""
斐波拉契扩展位服务
从2.py提取的斐波拉契计算逻辑
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict
import json
from ..redis_client import get_redis


class FibService:
    """斐波拉契服务类"""
    
    def __init__(self):
        # 初始化币安合约交易所
        exchange_config = {
            'rateLimit': 1200,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 合约模式
            }
        }
        # 如果设置了代理，使用代理
        import os
        proxy = os.getenv('BINANCE_PROXY')
        if proxy:
            exchange_config['proxies'] = {
                'http': proxy,
                'https': proxy
            }
        self.exchange = ccxt.binance(exchange_config)
        self.symbol = 'ETH/USDT:USDT'  # 币安USDT合约
        self.redis_client = get_redis()
    
    def calculate_fib_1618_30min(self, include_latest_completed: bool = True) -> Optional[Dict]:
        """
        计算30分钟时间窗口的斐波那契1.618扩展位（双向）
        include_latest_completed: 是否包含最新完成的K线参与计算
        返回上升和下降两个方向的扩展位
        """
        try:
            time_window_minutes = 30
            base_timeframe = '1m'
            required_candles = time_window_minutes + 15  # 额外15分钟缓冲
            
            # 获取分时K线数据
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, base_timeframe, limit=required_candles)
            
            if not ohlcv or len(ohlcv) < time_window_minutes + 1:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 计算K线实体价格
            df['body_top'] = df[['open', 'close']].max(axis=1)
            df['body_bottom'] = df[['open', 'close']].min(axis=1)
            df['body_size'] = df['body_top'] - df['body_bottom']
            
            # 根据参数决定是否包含最新K线
            if include_latest_completed:
                completed_data = df.iloc[:-1].copy()
            else:
                completed_data = df.iloc[:-2].copy()
            
            if len(completed_data) < time_window_minutes:
                return None
            
            # 获取当前价格（使用最新已完成K线的收盘价）
            current_price = completed_data.iloc[-1]['close']
            
            # 计算时间窗口
            reference_time = completed_data.iloc[-1]['datetime']
            window_start_time = reference_time - pd.Timedelta(minutes=time_window_minutes-1)
            
            # 筛选时间窗口内的数据
            window_data = completed_data[completed_data['datetime'] >= window_start_time].copy().reset_index(drop=True)
            
            if len(window_data) < 10:
                return None
            
            # 计算双向斐波那契扩展
            fib_results = self._calculate_dual_direction_extension(window_data, current_price, time_window_minutes)
            
            return fib_results
            
        except Exception as e:
            print(f"计算30分钟窗口斐波那契失败: {e}")
            return None
    
    def _calculate_dual_direction_extension(self, window_data, current_price, time_window_minutes):
        """计算双向斐波那契扩展位"""
        try:
            if len(window_data) < 5:
                return None
            
            # 确定A点和B点
            highest_shadow_price = window_data['high'].max()
            lowest_shadow_price = window_data['low'].min()
            
            highest_shadow_idx = window_data['high'].idxmax()
            lowest_shadow_idx = window_data['low'].idxmin()
            
            highest_candle = window_data.loc[highest_shadow_idx]
            lowest_candle = window_data.loc[lowest_shadow_idx]
            
            highest_body_top = highest_candle['body_top']
            lowest_body_bottom = lowest_candle['body_bottom']
            
            results = {'up': None, 'down': None}
            
            # 上升趋势计算（A=低点，B=高点）
            up_result = self._calculate_single_direction_extension(
                a_price=lowest_shadow_price,
                a_idx=lowest_shadow_idx,
                a_time=window_data.loc[lowest_shadow_idx]['datetime'].strftime('%H:%M'),
                b_price=highest_body_top,
                b_idx=highest_shadow_idx,
                b_time=window_data.loc[highest_shadow_idx]['datetime'].strftime('%H:%M'),
                window_data=window_data,
                trend='up',
                current_price=current_price,
                time_window_minutes=time_window_minutes
            )
            if up_result:
                results['up'] = up_result
            
            # 下降趋势计算（A=高点，B=低点）
            down_result = self._calculate_single_direction_extension(
                a_price=highest_shadow_price,
                a_idx=highest_shadow_idx,
                a_time=window_data.loc[highest_shadow_idx]['datetime'].strftime('%H:%M'),
                b_price=lowest_body_bottom,
                b_idx=lowest_shadow_idx,
                b_time=window_data.loc[lowest_shadow_idx]['datetime'].strftime('%H:%M'),
                window_data=window_data,
                trend='down',
                current_price=current_price,
                time_window_minutes=time_window_minutes
            )
            if down_result:
                results['down'] = down_result
            
            return results if (results['up'] or results['down']) else None
            
        except Exception as e:
            print(f"双向扩展计算失败: {e}")
            return None
    
    def _calculate_single_direction_extension(self, a_price, a_idx, a_time, 
                                             b_price, b_idx, b_time, 
                                             window_data, trend, current_price, 
                                             time_window_minutes):
        """单向斐波那契扩展计算"""
        try:
            if trend == 'up':
                # 上升趋势：A是低点，B是高点
                if b_idx + 1 < len(window_data):
                    after_b_data = window_data.iloc[b_idx+1:].copy()
                    if len(after_b_data) >= 2:
                        c_idx = after_b_data['low'].idxmin()
                        c_price = after_b_data.loc[c_idx]['low']
                    else:
                        search_start = max(0, b_idx - 5)
                        search_end = min(len(window_data), b_idx + 5)
                        search_data = window_data.iloc[search_start:search_end]
                        c_idx = search_data['low'].idxmin()
                        c_price = search_data.loc[c_idx]['low']
                else:
                    search_start = max(0, b_idx - 5)
                    search_data = window_data.iloc[search_start:b_idx]
                    if len(search_data) > 0:
                        c_idx = search_data['low'].idxmin()
                        c_price = search_data.loc[c_idx]['low']
                    else:
                        return None
                
                if c_price >= b_price:
                    if current_price < b_price and current_price > a_price:
                        c_price = current_price
                    else:
                        return None
                
                ab_range = b_price - a_price
                if ab_range <= 0:
                    return None
                
                fib_1618 = a_price + ab_range * 1.618
                
            else:  # down
                # 下降趋势：A是高点，B是低点
                if b_idx + 1 < len(window_data):
                    after_b_data = window_data.iloc[b_idx+1:].copy()
                    if len(after_b_data) >= 2:
                        c_idx = after_b_data['high'].idxmax()
                        c_price = after_b_data.loc[c_idx]['high']
                    else:
                        search_start = max(0, b_idx - 5)
                        search_end = min(len(window_data), b_idx + 5)
                        search_data = window_data.iloc[search_start:search_end]
                        c_idx = search_data['high'].idxmax()
                        c_price = search_data.loc[c_idx]['high']
                else:
                    search_start = max(0, b_idx - 5)
                    search_data = window_data.iloc[search_start:b_idx]
                    if len(search_data) > 0:
                        c_idx = search_data['high'].idxmax()
                        c_price = search_data.loc[c_idx]['high']
                    else:
                        return None
                
                if c_price <= b_price:
                    if current_price > b_price and current_price < a_price:
                        c_price = current_price
                    else:
                        return None
                
                ab_range = a_price - b_price
                if ab_range <= 0:
                    return None
                
                fib_1618 = a_price - ab_range * 1.618
            
            return {
                'fib_1618': fib_1618,
                'trend': trend,
                'a_price': a_price,
                'b_price': b_price,
                'c_price': c_price
            }
            
        except Exception as e:
            print(f"单向扩展计算失败({trend}): {e}")
            return None
    
    def cache_fib_levels(self, up_data: Optional[Dict], down_data: Optional[Dict]) -> bool:
        """
        缓存斐波拉契扩展位到Redis
        up_data: 上升方向的扩展位数据
        down_data: 下降方向的扩展位数据
        """
        try:
            cache_data = {
                'up': up_data,
                'down': down_data,
                'cached_at': datetime.now().isoformat()
            }
            
            # 缓存到Redis，24小时过期
            key = 'fib:ethusdt:30min'
            self.redis_client.setex(key, 86400, json.dumps(cache_data, default=str))
            
            return True
        except Exception as e:
            print(f"缓存斐波拉契点位失败: {e}")
            return False
    
    def get_cached_fib_levels(self) -> Optional[Dict]:
        """获取缓存的斐波拉契扩展位"""
        try:
            key = 'fib:ethusdt:30min'
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"获取缓存斐波拉契点位失败: {e}")
            return None
    
    def clear_fib_cache(self) -> bool:
        """清空斐波拉契缓存"""
        try:
            key = 'fib:ethusdt:30min'
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"清空斐波拉契缓存失败: {e}")
            return False



