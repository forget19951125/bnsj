"""
用户服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
from ..models.user import User


class UserService:
    """用户服务类"""
    
    @staticmethod
    def create_user(db: Session, username: str, password: str, expire_at: Optional[datetime] = None) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError(f"用户名 {username} 已存在")
        
        # 创建新用户
        hashed_password = User.hash_password(password)
        user = User(
            username=username,
            password=hashed_password,
            expire_at=expire_at,
            status=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def verify_user(db: Session, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        
        # 检查账号状态
        if user.status == 3:  # 已禁用
            return None
        
        # 检查账号是否过期
        if user.is_expired():
            # 更新状态为已过期
            user.status = 2
            db.commit()
            return None
        
        # 验证密码
        if not user.verify_password(password):
            return None
        
        return user
    
    @staticmethod
    def update_user_expire(db: Session, user_id: int, expire_at: Optional[datetime]) -> Optional[User]:
        """更新用户过期时间"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        user.expire_at = expire_at
        # 如果设置了过期时间且未过期，恢复状态为正常
        if expire_at and expire_at > datetime.now():
            if user.status == 2:  # 如果之前是已过期状态
                user.status = 1
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def check_user_valid(db: Session, user_id: int) -> bool:
        """检查用户是否有效（未过期、未禁用）"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        if user.status == 3:  # 已禁用
            return False
        
        if user.is_expired():
            # 更新状态为已过期
            user.status = 2
            db.commit()
            return False
        
        return True
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_users(db: Session) -> int:
        """获取用户总数"""
        return db.query(User).count()

