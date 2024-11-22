from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    check_id = Column(Integer, ForeignKey("checks.id"), nullable=False)

    check = relationship("Check", back_populates="products")
