"""
订单模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from ..database import Base


class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="订单ID")
    time_increments = Column(String(50), nullable=False, comment="时间增量，如TEN_MINUTE")
    symbol_name = Column(String(20), nullable=False, comment="交易对，如BTCUSDT")
    direction = Column(String(10), nullable=False, comment="方向：LONG或SHORT")
    valid_duration = Column(Integer, nullable=False, comment="有效时间（秒）")
    status = Column(Integer, default=1, index=True, comment="状态：1-待分配，2-已分配，3-已过期")
    assignment_count = Column(Integer, default=0, comment="分配次数")
    created_at = Column(DateTime, default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系（延迟导入避免循环依赖）
    # assignments = relationship("OrderAssignment", back_populates="order", cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "time_increments": self.time_increments,
            "symbol_name": self.symbol_name,
            "direction": self.direction,
            "valid_duration": self.valid_duration,
            "status": self.status,
            "assignment_count": self.assignment_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrderAssignment(Base):
    """订单分配记录表"""
    __tablename__ = "order_assignments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, comment="订单ID")
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    assigned_at = Column(DateTime, default=func.now(), index=True, comment="分配时间")
    executed_at = Column(DateTime, nullable=True, comment="执行时间")
    execution_result = Column(Text, nullable=True, comment="执行结果（JSON）")
    
    # 关系（延迟导入避免循环依赖）
    order = relationship("Order")
    user = relationship("User")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_result": self.execution_result,
        }

