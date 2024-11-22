from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Date
)
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Date, default=lambda: datetime.now().date())
    total = Column(Float, nullable=False)
    payment_type = Column(String, nullable=False)
    payment_amount = Column(Float, nullable=False)
    rest = Column(Float, nullable=False)
    user = relationship("User")

    products = relationship("Product", back_populates="check")
