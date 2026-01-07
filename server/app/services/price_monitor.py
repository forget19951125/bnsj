"""
价格监控服务
每秒获取ETHUSDT合约价格，计算RSI，检查是否触发订单生成
触发逻辑与2.py保持一致：只有当量能达到阈值时才计算斐波拉契
"""
import ccxt
import pandas as pd
import numpy as np
import time
import threading
from typing import Optional
from ..services.fib_service import FibService
from ..services.order_service import OrderService
from ..database import SessionLocal
from sqlalchemy.orm import Session


class PriceMonitor:
    """价格监控服务类"""
    
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
        self.fib_service = FibService()
        self.is_running = False
        self.monitor_thread = None
        self.price_tolerance = 0.01  # 价格容差（避免频繁触发）
        self.lock = threading.Lock()  # 防止重复生成订单
        self.last_error = None  # 记录最后一次错误
        
        # 量能触发相关（与2.py保持一致）
        self.volume_threshold = 45000  # 量能阈值：45k
        self.volume_triggered = False  # 量能触发标记
        self.trigger_timestamp = None  # 触发时间戳
        self.trigger_candle_timestamp = None  # 触发时的K线时间戳
    
    def calculate_rsi(self, period: int = 14, include_latest: bool = True) -> Optional[float]:
        """
        计算RSI指数（使用Wilder's平滑方法）
        include_latest: 是否包含最新完成的K线
        """
        try:
            # 获取足够的K线数据用于RSI计算（需要更多数据用于Wilder's平滑）
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=period + 20)
            
            if not ohlcv or len(ohlcv) < period + 1:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 如果include_latest为True，使用所有数据；否则排除最后一根未完成的K线
            if not include_latest:
                df = df.iloc[:-1]
            
            if len(df) < period + 1:
                return None
            
            # 计算价格变化
            delta = df['close'].diff()
            
            # 分离涨跌
            gain = delta.where(delta > 0, 0.0).values
            loss = (-delta.where(delta < 0, 0.0)).values
            
            # 使用Wilder's平滑方法计算RSI
            # 第一步：计算前period期的简单平均作为初始值
            avg_gain = np.zeros(len(gain))
            avg_loss = np.zeros(len(loss))
            
            # 初始值：前period期的简单平均（跳过第一个NaN）
            avg_gain[period] = np.mean(gain[1:period+1])
            avg_loss[period] = np.mean(loss[1:period+1])
            
            # 第二步：使用Wilder's平滑递归计算后续值
            # Wilder's公式: new_avg = (old_avg * (period-1) + current_value) / period
            for i in range(period + 1, len(gain)):
                avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i]) / period
                avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i]) / period
            
            # 计算RS和RSI
            # 避免除以0的情况（使用很小的阈值避免浮点数精度问题）
            final_avg_loss = avg_loss[-1]
            final_avg_gain = avg_gain[-1]
            
            if final_avg_loss < 1e-10:  # 使用很小的阈值，避免浮点数精度问题
                # 如果平均损失接近0，说明没有下跌，RSI应该是100
                return 100.0
            
            rs = final_avg_gain / final_avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # 返回最新的RSI值
            return float(rsi)
            
        except Exception as e:
            error_msg = str(e)
            self.last_error = error_msg
            print(f"[ERROR] 计算RSI失败: {error_msg}")
            # 如果是地区限制错误，给出提示
            if '451' in error_msg or 'restricted location' in error_msg.lower():
                print(f"[WARN] 币安API地区限制，请配置代理或使用其他数据源")
            return None
    
    def get_ethusdt_price(self) -> Optional[float]:
        """获取ETHUSDT合约价格"""
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            self.last_error = None
            return float(ticker['last'])
        except Exception as e:
            error_msg = str(e)
            self.last_error = error_msg
            # 使用print输出到pm2日志
            print(f"[ERROR] 获取ETHUSDT价格失败: {error_msg}")
            # 如果是地区限制错误，给出提示
            if '451' in error_msg or 'restricted location' in error_msg.lower():
                print(f"[WARN] 币安API地区限制，请配置代理或使用其他数据源")
            return None
    
    def get_realtime_volume(self) -> Optional[dict]:
        """
        获取实时量能（当前正在形成的1分钟K线）
        返回: {'timestamp': int, 'volume': float, 'price': float, ...}
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=1)
            
            if ohlcv and len(ohlcv) > 0:
                candle = ohlcv[0]
                timestamp = candle[0]
                volume = candle[5]  # 实时成交量
                close_price = candle[4]  # 当前价格
                open_price = candle[1]
                
                # 判断涨跌
                is_up = close_price >= open_price
                bar_color = "🟢" if is_up else "🔴"
                price_change_pct = ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0
                
                return {
                    'timestamp': timestamp,
                    'volume': volume,
                    'price': close_price,
                    'bar_color': bar_color,
                    'price_change_pct': price_change_pct,
                    'open': open_price,
                    'high': candle[2],
                    'low': candle[3]
                }
            return None
        except Exception as e:
            print(f"获取实时量能失败: {e}")
            return None
    
    def get_completed_candle_data(self, target_timestamp: Optional[int] = None) -> Optional[dict]:
        """
        获取已完成的K线数据
        target_timestamp: 目标K线时间戳，如果为None则返回最新完成的K线
        """
        try:
            # 获取最近的K线数据（至少2根，最后一根可能正在形成）
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=10)
            
            if not ohlcv or len(ohlcv) < 2:
                return None
            
            # 如果指定了目标时间戳，查找匹配的K线
            if target_timestamp:
                for candle in reversed(ohlcv[:-1]):  # 排除最后一根未完成的
                    if candle[0] == target_timestamp:
                        return {
                            'timestamp': candle[0],
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[5])
                        }
                # 如果没找到，返回最新完成的K线
                candle = ohlcv[-2]
            else:
                # 返回最新完成的K线（倒数第二根）
                candle = ohlcv[-2]
            
            return {
                'timestamp': candle[0],
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            }
        except Exception as e:
            print(f"获取已完成K线数据失败: {e}")
            return None
    
    def wait_for_candle_completion(self, trigger_candle_timestamp: int) -> bool:
        """
        等待触发量能的K线完成
        trigger_candle_timestamp: 触发时的K线时间戳
        """
        try:
            print(f"⏳ 等待K线完成 (时间戳: {trigger_candle_timestamp})...")
            
            wait_start = time.time()
            max_wait = 70  # 最多等待70秒
            
            while time.time() - wait_start < max_wait:
                # 获取最新的K线数据
                current_data = self.get_realtime_volume()
                
                if current_data:
                    current_timestamp = current_data['timestamp']
                    
                    # 如果当前K线的时间戳已经不同于触发时的时间戳
                    # 说明新的K线已经开始，触发的K线已经完成
                    if current_timestamp > trigger_candle_timestamp:
                        print(f"\n✅ K线已完成！新K线时间戳: {current_timestamp}")
                        # 额外等待2秒确保数据同步
                        time.sleep(2)
                        return True
                    
                    # 计算还需等待的时间
                    from datetime import datetime
                    current_time = datetime.now()
                    seconds_in_minute = current_time.second
                    remaining = 60 - seconds_in_minute
                    
                    # 显示倒计时
                    print(f"\r⏰ 等待K线完成: 约{remaining}秒", end="", flush=True)
                
                time.sleep(1)
            
            print(f"\n⚠️ 等待超时，继续执行...")
            return True
            
        except Exception as e:
            print(f"\n等待K线完成时出错: {e}")
            return False
    
    def _reset_trigger(self):
        """重置触发标记（60秒后）"""
        self.volume_triggered = False
        self.trigger_timestamp = None
        self.trigger_candle_timestamp = None
        print("🔄 触发标记已重置，可以再次检测量能")
    
    def get_last_completed_candle(self) -> Optional[dict]:
        """
        获取上一根已完成的分钟K线数据
        返回: {'open': float, 'close': float, 'high': float, 'low': float, 'timestamp': int}
        """
        return self.get_completed_candle_data()
    
    def check_short_price_condition(self, current_price: float) -> bool:
        """
        检查空单的额外价格条件
        当前价格 <= max(开盘价,收盘价) - (abs(开盘价 - 收盘价) / 3 * 2)
        """
        candle = self.get_last_completed_candle()
        if not candle:
            return False
        
        open_price = candle['open']
        close_price = candle['close']
        
        # 计算 max(开盘价,收盘价)
        max_oc = max(open_price, close_price)
        
        # 计算 abs(开盘价 - 收盘价) / 3 * 2
        body_size = abs(open_price - close_price)
        threshold = body_size / 3 * 2
        
        # 计算价格阈值
        price_threshold = max_oc - threshold
        
        # 检查条件：当前价格 <= 价格阈值
        result = current_price <= price_threshold
        
        if not result:
            print(f"空单价格条件未满足: 当前价格={current_price:.2f}, 阈值={price_threshold:.2f} (max_oc={max_oc:.2f}, body_size={body_size:.2f})")
        
        return result
    
    def check_long_price_condition(self, current_price: float) -> bool:
        """
        检查多单的额外价格条件
        当前价格 >= min(开盘价,收盘价) + (abs(开盘价 - 收盘价) / 3 * 2)
        """
        candle = self.get_last_completed_candle()
        if not candle:
            return False
        
        open_price = candle['open']
        close_price = candle['close']
        
        # 计算 min(开盘价,收盘价)
        min_oc = min(open_price, close_price)
        
        # 计算 abs(开盘价 - 收盘价) / 3 * 2
        body_size = abs(open_price - close_price)
        threshold = body_size / 3 * 2
        
        # 计算价格阈值
        price_threshold = min_oc + threshold
        
        # 检查条件：当前价格 >= 价格阈值
        result = current_price >= price_threshold
        
        if not result:
            print(f"多单价格条件未满足: 当前价格={current_price:.2f}, 阈值={price_threshold:.2f} (min_oc={min_oc:.2f}, body_size={body_size:.2f})")
        
        return result
    
    def check_and_create_orders(self, db: Session) -> bool:
        """
        检查价格和RSI条件，如果满足则创建订单
        返回True表示创建了订单，False表示未创建
        """
        try:
            # 获取缓存的斐波拉契点位
            cached_levels = self.fib_service.get_cached_fib_levels()
            if not cached_levels:
                return False
            
            up_data = cached_levels.get('up')
            down_data = cached_levels.get('down')
            
            if not up_data and not down_data:
                return False
            
            # 获取当前价格和RSI
            current_price = self.get_ethusdt_price()
            if current_price is None:
                return False
            
            rsi_value = self.calculate_rsi(include_latest=True)
            if rsi_value is None:
                return False
            
            # 检查上升扩展位条件（生成空单）
            if up_data and up_data.get('fib_1618'):
                up_level = up_data['fib_1618']
                # 检查：1) 价格达到扩展位 2) RSI >= 75 3) 当前价格满足K线价格条件
                if (current_price >= (up_level - self.price_tolerance) and 
                    rsi_value >= 75 and 
                    self.check_short_price_condition(current_price)):
                    print(f"触发空单条件: 价格={current_price:.2f}, 上升点位={up_level:.2f}, RSI={rsi_value:.2f}")
                    # [已屏蔽] 创建10分钟和30分钟空单
                    # self._create_orders(db, 'SHORT', current_price, rsi_value)
                    print(f"[已屏蔽] 空单创建功能已禁用，仅记录条件满足")
                    # 清空缓存
                    self.fib_service.clear_fib_cache()
                    return True
            
            # 检查下降扩展位条件（生成多单）
            if down_data and down_data.get('fib_1618'):
                down_level = down_data['fib_1618']
                # 检查：1) 价格达到扩展位 2) RSI <= 25 3) 当前价格满足K线价格条件
                if (current_price <= (down_level + self.price_tolerance) and 
                    rsi_value <= 25 and 
                    self.check_long_price_condition(current_price)):
                    print(f"触发多单条件: 价格={current_price:.2f}, 下降点位={down_level:.2f}, RSI={rsi_value:.2f}")
                    # [已屏蔽] 创建10分钟和30分钟多单
                    # self._create_orders(db, 'LONG', current_price, rsi_value)
                    print(f"[已屏蔽] 多单创建功能已禁用，仅记录条件满足")
                    # 清空缓存
                    self.fib_service.clear_fib_cache()
                    return True
            
            return False
            
        except Exception as e:
            print(f"检查订单条件失败: {e}")
            return False
    
    def _create_orders(self, db: Session, direction: str, price: float, rsi: float):
        """创建订单（10分钟和30分钟）"""
        try:
            # 使用锁防止重复生成
            if not self.lock.acquire(blocking=False):
                print("订单生成中，跳过本次检查")
                return
            
            try:
                # 创建10分钟订单
                order_10min = OrderService.create_order(
                    db=db,
                    time_increments='TEN_MINUTE',
                    symbol_name='ETHUSDT',
                    direction=direction,
                    valid_duration=5  # 订单有效期：5秒
                )
                print(f"✓ 创建10分钟订单: ID={order_10min.id}, 方向={direction}, 价格={price:.2f}, RSI={rsi:.2f}, 有效期=5秒")
                
                # 创建30分钟订单
                order_30min = OrderService.create_order(
                    db=db,
                    time_increments='THIRTY_MINUTE',
                    symbol_name='ETHUSDT',
                    direction=direction,
                    valid_duration=5  # 订单有效期：5秒
                )
                print(f"✓ 创建30分钟订单: ID={order_30min.id}, 方向={direction}, 价格={price:.2f}, RSI={rsi:.2f}, 有效期=5秒")
                
            finally:
                self.lock.release()
                
        except Exception as e:
            print(f"创建订单失败: {e}")
            if self.lock.locked():
                self.lock.release()
    
    def start_monitoring(self, db: Session = None):
        """
        启动价格监控（每秒检查一次）
        触发逻辑与2.py保持一致：只有当量能达到阈值时才计算斐波拉契
        """
        if self.is_running:
            print("价格监控已在运行")
            return
        
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                try:
                    # 每次循环都获取最新价格并计算RSI（确保价格和RSI总是最新的）
                    current_price = self.get_ethusdt_price()
                    current_rsi = self.calculate_rsi(include_latest=True)
                    
                    # 获取实时量能
                    volume_data = self.get_realtime_volume()
                    
                    if volume_data:
                        current_volume = volume_data['volume']
                        current_timestamp = volume_data['timestamp']
                        
                        # 检测到量能达到阈值且还未触发（与2.py逻辑一致）
                        if current_volume >= self.volume_threshold and not self.volume_triggered:
                            print(f"\n\n🚨 量能达到阈值！")
                            print(f"📍 触发时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"📊 当前量能: {current_volume:,.0f} (阈值: {self.volume_threshold:,})")
                            
                            # 标记已触发，记录K线时间戳
                            self.volume_triggered = True
                            self.trigger_timestamp = time.time()
                            self.trigger_candle_timestamp = current_timestamp
                            
                            print(f"⏳ 准备等待K线完成...")
                            
                            # 等待当前K线完成
                            wait_success = self.wait_for_candle_completion(current_timestamp)
                            
                            if wait_success:
                                print(f"✅ K线已完成，开始获取完整数据...")
                                
                                # 获取完整的K线数据（包括刚刚完成的触发K线）
                                completed_volume_data = self.get_completed_candle_data(current_timestamp)
                                
                                if completed_volume_data is None:
                                    print(f"⚠️ 未能获取到指定K线，使用最新完成的K线")
                                    completed_volume_data = self.get_completed_candle_data()
                                
                                if completed_volume_data:
                                    print(f"📊 完整量能: {completed_volume_data['volume']:,.0f}")
                                    
                                    # 计算斐波那契扩展位（包含最新完成的K线，双向）
                                    print(f"📐 正在计算双向斐波那契扩展位（包含触发K线）...")
                                    fib_result = self.fib_service.calculate_fib_1618_30min(include_latest_completed=True)
                                    
                                    if fib_result:
                                        up_data = fib_result.get('up')
                                        down_data = fib_result.get('down')
                                        
                                        # 显示计算结果
                                        up_status = "✅" if up_data else "⚠️"
                                        down_status = "✅" if down_data else "⚠️"
                                        print(f"{up_status}/{down_status} 30min 斐波那契计算完成（上升/下降）")
                                        
                                        # 缓存斐波拉契点位
                                        success = self.fib_service.cache_fib_levels(up_data=up_data, down_data=down_data)
                                        if success:
                                            up_str = f"${up_data['fib_1618']:.2f}" if up_data else "N/A"
                                            down_str = f"${down_data['fib_1618']:.2f}" if down_data else "N/A"
                                            print(f"✓ 斐波拉契点位已缓存: 上升={up_str}, 下降={down_str}")
                                        else:
                                            print(f"⚠️ 缓存斐波拉契点位失败")
                                    else:
                                        print(f"⚠️ 计算斐波拉契点位失败或数据不足")
                                    
                                    # 重置触发标记（60秒后）
                                    print(f"⏰ 将在60秒后重置触发标记\n")
                                    threading.Timer(60, self._reset_trigger).start()
                                else:
                                    print(f"❌ 无法获取完整K线数据")
                                    self.volume_triggered = False
                            else:
                                print(f"❌ 等待K线完成失败")
                                self.volume_triggered = False
                    
                    # 每次创建新的数据库会话
                    db = SessionLocal()
                    try:
                        # 检查条件并创建订单
                        self.check_and_create_orders(db)
                    finally:
                        db.close()
                    time.sleep(1)  # 每秒检查一次
                except Exception as e:
                    print(f"监控循环错误: {e}")
                    time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"✓ 价格监控已启动（每秒检查一次，量能阈值: {self.volume_threshold:,}）")
    
    def stop_monitoring(self):
        """停止价格监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("✓ 价格监控已停止")

