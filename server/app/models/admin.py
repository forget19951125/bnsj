"""
管理员模型
"""
from sqlalchemy import Column, BigInteger, String, DateTime, func
from ..database import Base


class Admin(Base):
    """管理员表"""
    __tablename__ = "admins"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="管理员ID")
    address = Column(String(42), unique=True, nullable=False, index=True, comment="以太坊地址")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

