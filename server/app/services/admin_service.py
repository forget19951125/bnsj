"""
管理员服务
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.admin import Admin


class AdminService:
    """管理员服务类"""
    
    @staticmethod
    def is_admin(db: Session, address: str) -> bool:
        """检查地址是否为管理员"""
        admin = db.query(Admin).filter(Admin.address == address.lower()).first()
        return admin is not None
    
    @staticmethod
    def add_admin(db: Session, address: str) -> Admin:
        """添加管理员"""
        address = address.lower()
        # 检查是否已存在
        existing = db.query(Admin).filter(Admin.address == address).first()
        if existing:
            return existing
        
        admin = Admin(address=address)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    @staticmethod
    def remove_admin(db: Session, address: str) -> bool:
        """移除管理员"""
        admin = db.query(Admin).filter(Admin.address == address.lower()).first()
        if admin:
            db.delete(admin)
            db.commit()
            return True
        return False
    
    @staticmethod
    def list_admins(db: Session) -> List[Admin]:
        """获取所有管理员"""
        return db.query(Admin).all()
    
    @staticmethod
    def get_admin_by_address(db: Session, address: str) -> Optional[Admin]:
        """根据地址获取管理员"""
        return db.query(Admin).filter(Admin.address == address.lower()).first()

