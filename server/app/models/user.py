"""
用户模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Integer, func
from sqlalchemy.orm import relationship
from ..database import Base
import bcrypt


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码（加密）")
    status = Column(Integer, default=1, index=True, comment="状态：1-正常，2-已过期，3-已禁用")
    expire_at = Column(DateTime, nullable=True, index=True, comment="账号过期时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系（延迟导入避免循环依赖）
    # order_assignments = relationship("OrderAssignment", back_populates="user", cascade="all, delete-orphan")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def is_expired(self) -> bool:
        """检查账号是否过期"""
        if self.status == 2:  # 已过期状态
            return True
        if self.expire_at:
            from datetime import datetime
            return datetime.now() > self.expire_at
        return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "status": self.status,
            "expire_at": self.expire_at.isoformat() if self.expire_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

