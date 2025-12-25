"""
Token管理工具
"""
import json
import os
from typing import Optional, Dict
from datetime import datetime
from ..config import settings


class TokenManager:
    """Token管理器"""
    
    def __init__(self):
        self.token_file = settings.token_file
        self.binance_token_file = settings.binance_token_file
    
    def save_token(self, token: str, user_id: int, username: str, expire_at: str):
        """保存登录Token"""
        data = {
            "token": token,
            "user_id": user_id,
            "username": username,
            "expire_at": expire_at,
            "login_time": datetime.now().isoformat()
        }
        with open(self.token_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_token(self) -> Optional[Dict]:
        """加载登录Token"""
        if not os.path.exists(self.token_file):
            return None
        
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 检查账号是否过期（expire_at是账号到期时间，不是token到期时间）
                expire_at_str = data.get("expire_at")
                if expire_at_str:
                    try:
                        expire_at = datetime.fromisoformat(expire_at_str)
                        if datetime.now() > expire_at:
                            # 账号已过期，清除token
                            self.clear_token()
                            return None
                    except:
                        # 日期解析失败，继续使用token
                        pass
                return data
        except Exception as e:
            # 文件读取失败，返回None
            print(f"加载token失败: {e}")
            return None
    
    def clear_token(self):
        """清除登录Token"""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
    
    def save_binance_token(self, csrftoken: str, p20t: str, expirationTimestamp: int):
        """保存币安Token"""
        data = {
            "csrftoken": csrftoken,
            "p20t": p20t,
            "expirationTimestamp": expirationTimestamp
        }
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.binance_token_file) if os.path.dirname(self.binance_token_file) else ".", exist_ok=True)
            with open(self.binance_token_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ Token已保存到: {self.binance_token_file}")
        except Exception as e:
            print(f"✗ Token保存失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def load_binance_token(self) -> Optional[Dict]:
        """加载币安Token"""
        if not os.path.exists(self.binance_token_file):
            return None
        
        try:
            with open(self.binance_token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 检查是否过期
                expirationTimestamp = data.get("expirationTimestamp", -1)
                if expirationTimestamp > 0:  # 只有当expirationTimestamp > 0时才检查过期
                    expire_time = datetime.fromtimestamp(expirationTimestamp)
                    if datetime.now() > expire_time:
                        print(f"Token已过期: {expire_time}")
                        return None
                # expirationTimestamp为-1或0时，认为不过期
                return data
        except Exception as e:
            print(f"加载币安Token失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clear_binance_token(self):
        """清除币安Token"""
        if os.path.exists(self.binance_token_file):
            os.remove(self.binance_token_file)
    
    def is_session_expired(self) -> bool:
        """检查会话是否过期（24小时）"""
        token_data = self.load_token()
        if not token_data:
            return True
        
        login_time = datetime.fromisoformat(token_data["login_time"])
        # 使用timedelta来正确计算过期时间
        from datetime import timedelta
        expire_time = login_time + timedelta(hours=settings.session_expire_hours)
        
        return datetime.now() > expire_time

