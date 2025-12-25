"""
认证服务
"""
from typing import Optional, Dict
from ..api_client import APIClient
from ..utils.token_manager import TokenManager


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.api_client = APIClient()
        self.token_manager = TokenManager()
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        result = self.api_client.login(username, password)
        
        if result.get("code") == 200 and result.get("data"):
            data = result["data"]
            self.token_manager.save_token(
                token=data["token"],
                user_id=data["user_id"],
                username=data["username"],
                expire_at=data["expire_at"]
            )
            self.api_client.set_token(data["token"])
        
        return result
    
    def load_session(self) -> bool:
        """加载已保存的会话"""
        token_data = self.token_manager.load_token()
        if not token_data:
            return False
        
        # 检查会话是否过期（24小时）
        if self.token_manager.is_session_expired():
            self.token_manager.clear_token()
            return False
        
        # 验证Token是否有效（单点登录检查）
        try:
            self.api_client.set_token(token_data["token"])
            verify_result = self.api_client.verify_token()
            if verify_result.get("code") == 200:
                return True
            else:
                # Token已失效（可能在别处登录），清除本地token
                self.token_manager.clear_token()
                return False
        except Exception as e:
            # Token验证失败（可能是单点登录导致），清除本地token
            self.token_manager.clear_token()
            return False
    
    def logout(self):
        """退出登录"""
        self.token_manager.clear_token()
        self.api_client.set_token(None)
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        token_data = self.token_manager.load_token()
        return token_data

