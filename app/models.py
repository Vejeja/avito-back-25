import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    coins = Column(Integer, default=1000, nullable=False)

    transactions_sent = relationship(
        "Transaction", back_populates="sender", foreign_keys="Transaction.from_user_id"
    )
    transactions_received = relationship(
        "Transaction", back_populates="receiver", foreign_keys="Transaction.to_user_id"
    )
    purchases = relationship("Purchase", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    sender = relationship("User", foreign_keys=[from_user_id], back_populates="transactions_sent")
    receiver = relationship("User", foreign_keys=[to_user_id], back_populates="transactions_received")

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="purchases")
