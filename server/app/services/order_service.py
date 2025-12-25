"""
订单服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional, List
from ..models.order import Order, OrderAssignment
from ..models.user import User
from ..redis_client import get_redis
import json


class OrderService:
    """订单服务类"""
    
    @staticmethod
    def create_order(
        db: Session,
        time_increments: str,
        symbol_name: str,
        direction: str,
        valid_duration: int
    ) -> Order:
        """创建订单"""
        order = Order(
            time_increments=time_increments,
            symbol_name=symbol_name,
            direction=direction,
            valid_duration=valid_duration,
            status=1  # 待分配
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # 缓存订单信息到Redis
        redis_client = get_redis()
        order_key = f"order:cache:{order.id}"
        redis_client.setex(
            order_key,
            valid_duration + 3600,  # 订单有效期 + 1小时
            json.dumps(order.to_dict(), default=str)
        )
        
        return order
    
    @staticmethod
    def pull_order(db: Session, user_id: int) -> Optional[Order]:
        """拉取订单（带去重逻辑）"""
        redis_client = get_redis()
        
        # 1. 查询待分配的订单
        pending_orders = db.query(Order).filter(Order.status == 1).order_by(Order.created_at).all()
        
        if not pending_orders:
            return None
        
        # 2. 过滤已过期的订单
        current_time = datetime.now()
        valid_orders = []
        for order in pending_orders:
            elapsed = (current_time - order.created_at).total_seconds()
            if elapsed < order.valid_duration:
                valid_orders.append(order)
            else:
                # 标记为已过期
                order.status = 3
                db.commit()
        
        if not valid_orders:
            return None
        
        # 3. 检查用户是否已拉取（Redis去重）
        for order in valid_orders:
            key = f"order:assigned:{order.id}:{user_id}"
            if not redis_client.exists(key):
                # 4. 标记为已拉取（该用户已拉取此订单）
                redis_client.setex(key, order.valid_duration + 3600, "1")
                
                # 5. 记录到数据库
                assignment = OrderAssignment(
                    order_id=order.id,
                    user_id=user_id,
                    assigned_at=current_time
                )
                db.add(assignment)
                
                # 6. 增加分配次数（每个用户拉取一次，分配次数+1）
                order.assignment_count = (order.assignment_count or 0) + 1
                # 如果有分配记录，状态改为已分配
                if order.assignment_count > 0:
                    order.status = 2
                db.commit()
                
                return order
        
        return None
    
    @staticmethod
    def mark_order_assigned(db: Session, order_id: int, user_id: int) -> bool:
        """标记订单已分配（用于客户端确认）"""
        redis_client = get_redis()
        key = f"order:assigned:{order_id}:{user_id}"
        
        # 检查是否已存在分配记录
        assignment = db.query(OrderAssignment).filter(
            and_(
                OrderAssignment.order_id == order_id,
                OrderAssignment.user_id == user_id
            )
        ).first()
        
        if not assignment:
            # 创建分配记录
            assignment = OrderAssignment(
                order_id=order_id,
                user_id=user_id,
                assigned_at=datetime.now()
            )
            db.add(assignment)
            db.commit()
        
        # 确保Redis中有记录
        if not redis_client.exists(key):
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                redis_client.setex(key, order.valid_duration + 3600, "1")
        
        return True
    
    @staticmethod
    def record_order_result(
        db: Session,
        order_id: int,
        user_id: int,
        result: dict
    ) -> bool:
        """记录订单执行结果"""
        assignment = db.query(OrderAssignment).filter(
            and_(
                OrderAssignment.order_id == order_id,
                OrderAssignment.user_id == user_id
            )
        ).first()
        
        if assignment:
            assignment.executed_at = datetime.now()
            assignment.execution_result = json.dumps(result, ensure_ascii=False)
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
        """根据ID获取订单"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    @staticmethod
    def list_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
        """获取订单列表"""
        return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_orders(db: Session) -> int:
        """获取订单总数"""
        return db.query(Order).count()

