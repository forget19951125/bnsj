import ccxt
import pandas as pd
import numpy as np
import time
import requests
import json
from datetime import datetime
import pytz
import threading
import warnings
warnings.filterwarnings('ignore')

class ETHRealtimeFib1618Monitor:
    def __init__(self, dingtalk_webhook_url=None):
        # 初始化币安合约交易所
        self.exchange = ccxt.binance({
            'rateLimit': 1200,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # 合约模式
            }
        })
        
        self.symbol = 'ETH/USDT:USDT'  # 币安USDT合约
        self.volume_threshold = 45000  # 重量阈值：45k
        self.dingtalk_webhook_url = dingtalk_webhook_url
        self.beijing_tz = pytz.timezone('Asia/Shanghai')
        
        # 简化的机器人功能
        self.last_query_time = 0
        self.query_cooldown = 10  # 10秒冷却时间
        
        # 量能触发等待标记
        self.volume_triggered = False
        self.trigger_timestamp = None
        self.trigger_candle_timestamp = None  # 记录触发时的K线时间戳
        
    def get_beijing_time(self):
        """获取北京时间"""
        utc_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        beijing_time = utc_time.astimezone(self.beijing_tz)
        return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def calculate_rsi(self, period=14, include_latest=True):
        """
        计算RSI指数
        include_latest: 是否包含最新完成的K线
        """
        try:
            # 获取足够的K线数据用于RSI计算
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=period + 10)
            
            if not ohlcv or len(ohlcv) < period + 1:
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 如果include_latest为True，使用所有数据；否则排除最后一根未完成的K线
            if not include_latest:
                df = df.iloc[:-1]
            
            # 计算价格变化
            delta = df['close'].diff()
            
            # 分离涨跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # 计算RS和RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 返回最新的RSI值
            return rsi.iloc[-1]
            
        except Exception as e:
            print(f"计算RSI失败: {e}")
            return None
    
    def get_realtime_volume(self):
        """获取实时重量（当前正在形成的1分钟K线）"""
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
            print(f"获取实时重量失败: {e}")
            return None
    
    def get_completed_candle_data(self, candle_timestamp=None):
        """
        获取已完成的K线数据
        candle_timestamp: 如果指定，获取该时间戳对应的已完成K线
        """
        try:
            # 获取最近的K线数据
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=5)
            
            if not ohlcv or len(ohlcv) < 2:
                return None
            
            # 如果指定了时间戳，查找对应的K线
            if candle_timestamp:
                for candle in ohlcv:
                    if candle[0] == candle_timestamp:
                        return {
                            'timestamp': candle[0],
                            'volume': candle[5],
                            'price': candle[4],
                            'open': candle[1],
                            'high': candle[2],
                            'low': candle[3],
                            'close': candle[4],
                            'bar_color': "🟢" if candle[4] >= candle[1] else "🔴",
                            'price_change_pct': ((candle[4] - candle[1]) / candle[1]) * 100 if candle[1] > 0 else 0
                        }
            
            # 否则返回倒数第二根K线（最后一根已完成的）
            # 因为最后一根可能正在形成中
            completed_candle = ohlcv[-2]
            
            return {
                'timestamp': completed_candle[0],
                'volume': completed_candle[5],
                'price': completed_candle[4],
                'open': completed_candle[1],
                'high': completed_candle[2],
                'low': completed_candle[3],
                'close': completed_candle[4],
                'bar_color': "🟢" if completed_candle[4] >= completed_candle[1] else "🔴",
                'price_change_pct': ((completed_candle[4] - completed_candle[1]) / completed_candle[1]) * 100 if completed_candle[1] > 0 else 0
            }
            
        except Exception as e:
            print(f"获取已完成K线数据失败: {e}")
            return None
    
    def calculate_fib_1618_by_timewindow(self, time_window_minutes, include_latest_completed=True):
        """
        根据时间窗口计算斐波那契1.618扩展位（双向）
        include_latest_completed: 是否包含最新完成的K线参与计算
        返回上升和下降两个方向的扩展位
        """
        try:
            # 使用1分钟K线作为基础数据（精度最高）
            base_timeframe = '1m'
            
            # 计算需要获取的K线数量 = 时间窗口 + 额外缓冲
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
                # 包含所有已完成的K线，包括最新完成的那根
                # 最后一根可能正在形成，所以排除
                completed_data = df.iloc[:-1].copy()
            else:
                # 排除最后两根K线
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
            print(f"计算{time_window_minutes}分钟窗口斐波那契失败: {e}")
            return None

    def _calculate_dual_direction_extension(self, window_data, current_price, time_window_minutes):
        """
        计算双向斐波那契扩展位
        返回上升和下降两个方向的结果
        """
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
        """
        单向斐波那契扩展计算（已优化，移除严格的时间顺序限制）
        """
        try:
            # 计算AB范围
            if trend == 'up':
                # 上升趋势：A是低点，B是高点
                # 寻找C点：在整个窗口中找一个回调低点
                # C点应该：1) 低于B点  2) 高于A点
                
                # 优先在B点之后寻找C点
                if b_idx + 1 < len(window_data):
                    after_b_data = window_data.iloc[b_idx+1:].copy()
                    if len(after_b_data) >= 2:
                        c_idx = after_b_data['low'].idxmin()
                        c_price = after_b_data.loc[c_idx]['low']
                    else:
                        # 如果B点之后数据不足，在B点前后小范围内找
                        search_start = max(0, b_idx - 5)
                        search_end = min(len(window_data), b_idx + 5)
                        search_data = window_data.iloc[search_start:search_end]
                        c_idx = search_data['low'].idxmin()
                        c_price = search_data.loc[c_idx]['low']
                else:
                    # B点已经是最后的数据，在前面找
                    search_start = max(0, b_idx - 5)
                    search_data = window_data.iloc[search_start:b_idx]
                    if len(search_data) > 0:
                        c_idx = search_data['low'].idxmin()
                        c_price = search_data.loc[c_idx]['low']
                    else:
                        return None
                
                # 验证C点的有效性
                if c_price >= b_price:  # C不能高于或等于B
                    # 如果找到的C点无效，尝试使用当前价格作为C点
                    if current_price < b_price and current_price > a_price:
                        c_price = current_price
                    else:
                        return None
                
                # 计算斐波那契1.618扩展位
                ab_range = b_price - a_price
                if ab_range <= 0:
                    return None
                
                fib_1618 = a_price + ab_range * 1.618
                
            else:  # down
                # 下降趋势：A是高点，B是低点
                # 寻找C点：在整个窗口中找一个反弹高点
                # C点应该：1) 高于B点  2) 低于A点
                
                # 优先在B点之后寻找C点
                if b_idx + 1 < len(window_data):
                    after_b_data = window_data.iloc[b_idx+1:].copy()
                    if len(after_b_data) >= 2:
                        c_idx = after_b_data['high'].idxmax()
                        c_price = after_b_data.loc[c_idx]['high']
                    else:
                        # 如果B点之后数据不足，在B点前后小范围内找
                        search_start = max(0, b_idx - 5)
                        search_end = min(len(window_data), b_idx + 5)
                        search_data = window_data.iloc[search_start:search_end]
                        c_idx = search_data['high'].idxmax()
                        c_price = search_data.loc[c_idx]['high']
                else:
                    # B点已经是最后的数据，在前面找
                    search_start = max(0, b_idx - 5)
                    search_data = window_data.iloc[search_start:b_idx]
                    if len(search_data) > 0:
                        c_idx = search_data['high'].idxmax()
                        c_price = search_data.loc[c_idx]['high']
                    else:
                        return None
                
                # 验证C点的有效性
                if c_price <= b_price:  # C不能低于或等于B
                    # 如果找到的C点无效，尝试使用当前价格作为C点
                    if current_price > b_price and current_price < a_price:
                        c_price = current_price
                    else:
                        return None
                
                # 计算斐波那契1.618扩展位
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

    def get_all_fib_1618(self, include_latest_completed=True):
        """
        获取所有时间窗口的1.618扩展位（双向）
        include_latest_completed: 是否包含最新完成的K线
        """
        time_windows = [30, 120, 240]  # 30分钟、2小时、4小时
        fib_data = {}
        
        for minutes in time_windows:
            if minutes == 30:
                key = '30min'
            elif minutes == 120:
                key = '2hour'
            elif minutes == 240: 
                key = '4hour'
            
            fib_data[key] = self.calculate_fib_1618_by_timewindow(minutes, include_latest_completed)
        
        return fib_data
    
    def send_instant_alert(self, volume_data, fib_data, rsi_value):
        """发送精简告警到钉钉 - 包含量能、双向斐波那契扩展位和RSI"""
        timestamp = self.get_beijing_time()
        
        # 格式化K线时间
        candle_time = datetime.fromtimestamp(volume_data['timestamp']/1000, tz=self.beijing_tz).strftime("%H:%M")
        
        message = f"""🚨 ETH重量爆发告警 🚨

⏰ 告警时间: {timestamp}
📅 K线时间: {candle_time}
🔥 完整量能: {volume_data['volume']:,.0f}
{volume_data['bar_color']} 价格: ${volume_data['price']:.2f} ({volume_data['price_change_pct']:+.2f}%)
📊 RSI(14): {rsi_value:.2f}

📈 斐波那契1.618扩展位（双向）:"""

        window_names = {
            '30min': '30分钟',
            '2hour': '2小时',
            '4hour': '4小时'
        }

        for timeframe, data in fib_data.items():
            window_name = window_names.get(timeframe, timeframe)
            
            if data:
                message += f"\n\n🕐 {window_name}:"
                
                # 上升方向
                if data.get('up'):
                    up_data = data['up']
                    message += f"\n  📈 上升1.618: ${up_data['fib_1618']:.2f}"
                    message += f"\n     (A=${up_data['a_price']:.2f} → B=${up_data['b_price']:.2f} → C=${up_data['c_price']:.2f})"
                else:
                    message += f"\n  📈 上升1.618: 计算中..."
                
                # 下降方向
                if data.get('down'):
                    down_data = data['down']
                    message += f"\n  📉 下降1.618: ${down_data['fib_1618']:.2f}"
                    message += f"\n     (A=${down_data['a_price']:.2f} → B=${down_data['b_price']:.2f} → C=${down_data['c_price']:.2f})"
                else:
                    message += f"\n  📉 下降1.618: 计算中..."
            else:
                message += f"\n\n🕐 {window_name}: 数据计算中..."

        message += f"\n\n💡 该量能K线已包含在斐波那契计算中"
        message += f"\n💡 已同时播报多空双向1.618扩展位"

        # if self.dingtalk_webhook_url:
        #     try:
        #         data_to_send = {
        #             "msgtype": "text",
        #             "text": {
        #                 "content": message
        #             },
        #             "at": {
        #                 "isAtAll": True
        #             }
        #         }
                
        #         headers = {'Content-Type': 'application/json'}
        #         response = requests.post(
        #             self.dingtalk_webhook_url, 
        #             data=json.dumps(data_to_send), 
        #             headers=headers,
        #             timeout=10
        #         )
                
        #         if response.status_code == 200:
        #             result = response.json()
        #             if result.get('errcode') == 0:
        #                 print("✅ 告警已发送到钉钉（含双向扩展位）")
        #                 return True
        #             else:
        #                 print(f"❌ 钉钉告警发送失败: {result.get('errmsg')}")
        #                 return False
        #         else:
        #             print(f"❌ 钉钉告警发送失败，状态码: {response.status_code}")
        #             return False
        #     except Exception as e:
        #         print(f"❌ 发送钉钉告警失败: {e}")
        #         return False
        # else:
        #     print("⚠️ 未配置钉钉告警")
        #     return False
    
    def wait_for_candle_completion(self, trigger_candle_timestamp):
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
    
    def test_dingtalk_connection(self):
        """测试钉钉机器人连接"""
        print("🔗 正在测试钉钉机器人连接...")
        
        if not self.dingtalk_webhook_url:
            print("❌ 未配置钉钉Webhook URL")
            return False
        
        timestamp = self.get_beijing_time()
        test_message = f"""🤖 ETH监控机器人连接测试

⏰ 测试时间: {timestamp}
🔗 连接状态: ✅ 成功
📊 监控配置: ETH实时重量监控
⚡ 告警阈值: {self.volume_threshold:,}
🎯 分析功能: 双向斐波那契1.618扩展位
📈 RSI指标: 已启用

💡 优化特性:
  • 量能达到后等待K线完成
  • 播报完整K线量能数据
  • 斐波那契计算包含触发K线
  • 多空双向1.618扩展位（已修复）
  • 同时显示上升和下降两个方向

🚀 机器人已就绪，开始监控..."""

        try:
            data = {
                "msgtype": "text",
                "text": {
                    "content": test_message
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.dingtalk_webhook_url, 
                data=json.dumps(data), 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200 and response.json().get('errcode') == 0:
                print("✅ 钉钉机器人连接测试成功")
                return True
            else:
                print("❌ 钉钉机器人连接测试失败")
                return False
        except Exception as e:
            print(f"❌ 钉钉连接测试出错: {e}")
            return False
    
    def run_monitor_with_periodic_commands(self):
        """运行监控（优化版本）"""
        print("🚀 开始ETH实时重量监控...")
        print(f"📊 监控模式: 每秒检测重量，30秒汇总一次")
        print(f"⚡ 重量阈值: {self.volume_threshold:,}")
        print(f"📈 关键特性:")
        print(f"   • 量能达到后等待K线完成")
        print(f"   • 播报完整K线量能")
        print(f"   • 斐波那契计算包含触发K线")
        print(f"   • 多空双向1.618扩展位（已修复）")
        print(f"   • 同时显示上升和下降方向")
        print("按 Ctrl+C 停止监控\n")
        
        try:
            while True:
                max_volume = 0
                max_volume_time = ""
                check_count = 0
                
                print(f"🔄 开始30秒监控周期...")
                
                for i in range(30):
                    try:
                        volume_data = self.get_realtime_volume()
                        
                        if volume_data:
                            check_count += 1
                            current_volume = volume_data['volume']
                            current_timestamp = volume_data['timestamp']
                            
                            if current_volume > max_volume:
                                max_volume = current_volume
                                max_volume_time = self.get_beijing_time()
                            
                            progress = f"[{i+1:2d}/30]"
                            status = f"实时重量: {current_volume:,.0f} | 最大: {max_volume:,.0f}"
                            
                            # 检测到量能达到阈值且还未触发
                            if current_volume >= self.volume_threshold and not self.volume_triggered:
                                print(f"\r{progress} {status} 🚨", end="", flush=True)
                                print(f"\n\n🚨 重量达到阈值！")
                                print(f"📍 触发时间: {self.get_beijing_time()}")
                                print(f"📊 当前量能: {current_volume:,.0f}")
                                
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
                                        
                                        # 计算RSI（包含最新完成的K线）
                                        print(f"📈 正在计算RSI...")
                                        rsi_value = self.calculate_rsi(include_latest=True)
                                        if rsi_value is None:
                                            rsi_value = 0.0
                                        print(f"✅ RSI: {rsi_value:.2f}")
                                        
                                        # 计算斐波那契扩展位（包含最新完成的K线，双向）
                                        print(f"📐 正在计算双向斐波那契扩展位（包含触发K线）...")
                                        fib_data = self.get_all_fib_1618(include_latest_completed=True)
                                        
                                        # 显示计算结果
                                        if fib_data:
                                            for timeframe, data in fib_data.items():
                                                if data:
                                                    up_status = "✅" if data.get('up') else "⚠️"
                                                    down_status = "✅" if data.get('down') else "⚠️"
                                                    print(f"{up_status}/{down_status} {timeframe} 斐波那契计算完成（上升/下降）")
                                        
                                        # 发送告警
                                        print(f"📤 正在发送双向告警...")
                                        send_success = self.send_instant_alert(completed_volume_data, fib_data, rsi_value)
                                        
                                        if send_success:
                                            print(f"🎉 双向告警发送成功！")
                                        else:
                                            print(f"⚠️ 告警发送失败")
                                        
                                        # 重置触发标记（60秒后）
                                        print(f"⏰ 将在60秒后重置触发标记\n")
                                        threading.Timer(60, self._reset_trigger).start()
                                    else:
                                        print(f"❌ 无法获取完整K线数据")
                                        self.volume_triggered = False
                                else:
                                    print(f"❌ 等待K线完成失败")
                                    self.volume_triggered = False
                                
                            else:
                                print(f"\r{progress} {status}", end="", flush=True)
                        
                        time.sleep(1)
                    except Exception as e:
                        print(f"\n⚠️ 第{i+1}秒检测失败: {e}")
                        continue
                
                print(f"\n📋 30秒周期总结:")
                print(f"   检测次数: {check_count}")
                print(f"   最大量能: {max_volume:,.0f}")
                if max_volume_time:
                    print(f"   发生时间: {max_volume_time}")
                print()
                
        except KeyboardInterrupt:
            print("\n⏹️ 监控已停止")
        except Exception as e:
            print(f"❌ 监控出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _reset_trigger(self):
        """重置触发标记"""
        self.volume_triggered = False
        self.trigger_timestamp = None
        self.trigger_candle_timestamp = None
        print("🔄 触发标记已重置，可以再次检测量能")


# 自动运行部分
if __name__ == "__main__":
    print("🤖 ETH实时重量监控启动")
    print("="*70)
    print("⚡ 核心功能:")
    print("   1. 每秒监控实时重量")
    print("   2. 达到45K阈值后等待K线完成")
    print("   3. 播报完整K线的量能数据")
    print("   4. 斐波那契计算包含触发量能的K线")
    print("   5. 多空双向1.618扩展位分析（已修复）")
    print("   6. 同时播报上升和下降两个方向")
    print("   7. RSI指标监控")
    print("="*70)
    
    # 钉钉配置
    dingtalk_webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=40b321aa20cebebaaf6b001a6a1f7ddead1289cfe7cd859a4fef8a14b459338d"
    volume_threshold = 45000
    
    print(f"✅ 钉钉告警已配置")
    print(f"✅ 重量阈值: {volume_threshold:,}")
    
    # 创建监控实例
    monitor = ETHRealtimeFib1618Monitor(dingtalk_webhook_url=dingtalk_webhook_url)
    monitor.volume_threshold = volume_threshold
    
    # 测试钉钉连接
    connection_ok = monitor.test_dingtalk_connection()
    
    if not connection_ok:
        print("⚠️ 警告: 钉钉机器人连接失败，但监控将继续运行")
        print("请检查Webhook URL是否正确")
    else:
        print("🎉 系统检查通过，所有功能就绪")
    
    print(f"\n{'='*70}")
    print(f"🚀 开始监控...")
    print(f"{'='*70}\n")
    
    # 运行监控
    monitor.run_monitor_with_periodic_commands()
