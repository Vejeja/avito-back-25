from pydantic import BaseModel
from typing import List, Optional

# Схемы для аутентификации
class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    token: str

# Схема для перевода монет
class SendCoinRequest(BaseModel):
    toUser: str
    amount: int

# Схема элемента инвентаря
class InventoryItem(BaseModel):
    type: str
    quantity: int

# Схема записи транзакции
class TransactionRecord(BaseModel):
    fromUser: Optional[str] = None
    toUser: Optional[str] = None
    amount: int

# Схема истории монет
class CoinHistory(BaseModel):
    received: List[TransactionRecord]
    sent: List[TransactionRecord]

# Схема ответа /api/info
class InfoResponse(BaseModel):
    coins: int
    inventory: List[InventoryItem]
    coinHistory: CoinHistory

    class Config:
        orm_mode = True

# Схема ответа об ошибке
class ErrorResponse(BaseModel):
    errors: str
