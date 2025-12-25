"""
服务器API客户端
"""
import requests
from typing import Optional, Dict, Any
from .config import settings


class APIClient:
    """API客户端类"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.server_url
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """设置认证Token"""
        self.token = token
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        url = f"{self.base_url}/api/auth/login"
        response = requests.post(
            url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 200 and data.get("data"):
            self.set_token(data["data"]["token"])
        
        return data
    
    def verify_token(self) -> Dict[str, Any]:
        """验证Token"""
        url = f"{self.base_url}/api/auth/verify"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def send_heartbeat(self) -> bool:
        """发送心跳"""
        url = f"{self.base_url}/api/auth/heartbeat"
        try:
            response = requests.post(url, headers=self._get_headers())
            if response.status_code == 401:
                raise Exception("Token已失效，请重新登录")
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Token已失效，请重新登录")
            raise
        except Exception as e:
            # 心跳失败不应该影响主流程，只记录错误
            return False
    
    def pull_order(self) -> Optional[Dict[str, Any]]:
        """拉取订单"""
        url = f"{self.base_url}/api/orders/pull"
        try:
            response = requests.get(url, headers=self._get_headers())
            # 检查HTTP状态码
            if response.status_code == 401:
                # 尝试获取详细的错误信息
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", "")
                    if "账号已过期" in detail or "已禁用" in detail:
                        raise Exception("账号已过期或已禁用，请重新登录")
                    else:
                        raise Exception("Token已失效，请重新登录")
                except:
                    raise Exception("Token已失效，请重新登录")
            response.raise_for_status()
            
            # 检查响应内容
            try:
                data = response.json()
            except:
                raise Exception("服务器响应格式错误")
            
            # 检查data是否为None
            if data is None:
                return None
            
            # 检查业务状态码
            if data.get("code") == 401 or data.get("code") == 403:
                message = data.get("message", "") or data.get("detail", "")
                if "账号已过期" in message or "已禁用" in message:
                    raise Exception("账号已过期或已禁用，请重新登录")
                else:
                    raise Exception("Token已失效，请重新登录")
            
            if data.get("code") == 200:
                data_obj = data.get("data")
                if data_obj is None:
                    return None
                # 服务器返回的data就是订单对象本身，不是嵌套在order字段中
                if isinstance(data_obj, dict):
                    # 如果data_obj有order字段，使用order字段；否则直接使用data_obj
                    return data_obj.get("order") if "order" in data_obj else data_obj
                return None
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Token已失效，请重新登录")
            raise
        except Exception as e:
            # 重新抛出已知的异常
            if "Token已失效" in str(e) or "响应格式错误" in str(e):
                raise
            # 其他异常包装一下
            raise Exception(f"拉取订单失败: {str(e)}")
    
    def mark_order_assigned(self, order_id: int) -> bool:
        """标记订单已拉取"""
        url = f"{self.base_url}/api/orders/mark-assigned"
        response = requests.post(
            url,
            json={"order_id": order_id},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return True
    
    def record_order_result(self, order_id: int, result: Dict[str, Any]) -> bool:
        """记录订单执行结果"""
        url = f"{self.base_url}/api/orders/record-result"
        response = requests.post(
            url,
            json={"order_id": order_id, "result": result},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return True

