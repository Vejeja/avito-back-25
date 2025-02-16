import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import SessionLocal, engine
from app.settings import settings

# Создание таблиц в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Настройки безопасности
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Справочник мерча (название: цена)
MERCH_ITEMS = {
    "t-shirt": 80,
    "cup": 20,
    "book": 50,
    "pen": 10,
    "powerbank": 200,
    "hoody": 300,
    "umbrella": 200,
    "socks": 10,
    "wallet": 50,
    "pink-hoody": 500,
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/api/auth", response_model=schemas.AuthResponse)
def auth(auth_request: schemas.AuthRequest, db: Session = Depends(get_db)):
    user = get_user_by_username(db, auth_request.username)
    if not user:
        # Автоматическая регистрация нового пользователя с 1000 монетами
        hashed_password = get_password_hash(auth_request.password)
        user = models.User(username=auth_request.username, hashed_password=hashed_password, coins=1000)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not verify_password(auth_request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    access_token = create_access_token(data={"sub": user.username})
    return schemas.AuthResponse(token=access_token)

@app.get("/api/info", response_model=schemas.InfoResponse)
def get_info(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Подсчет купленного мерча (инвентарь)
    purchases = db.query(models.Purchase).filter(models.Purchase.user_id == current_user.id).all()
    inventory_dict = {}
    for purchase in purchases:
        inventory_dict[purchase.item] = inventory_dict.get(purchase.item, 0) + 1
    inventory = [{"type": item, "quantity": qty} for item, qty in inventory_dict.items()]
    
    # История перевода монет
    transactions_received = db.query(models.Transaction).filter(models.Transaction.to_user_id == current_user.id).all()
    transactions_sent = db.query(models.Transaction).filter(models.Transaction.from_user_id == current_user.id).all()
    
    received = [
        {"fromUser": db.query(models.User).get(tx.from_user_id).username, "amount": tx.amount}
        for tx in transactions_received
    ]
    sent = [
        {"toUser": db.query(models.User).get(tx.to_user_id).username, "amount": tx.amount}
        for tx in transactions_sent
    ]
    
    return schemas.InfoResponse(
        coins=current_user.coins,
        inventory=inventory,
        coinHistory={"received": received, "sent": sent},
    )

@app.post("/api/sendCoin")
def send_coin(
    request: schemas.SendCoinRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if request.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
    if current_user.coins < request.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient coins")
    
    recipient = get_user_by_username(db, request.toUser)
    if not recipient:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient not found")
    
    # Перевод монет: списываем у отправителя и начисляем получателю
    current_user.coins -= request.amount
    recipient.coins += request.amount
    tx = models.Transaction(from_user_id=current_user.id, to_user_id=recipient.id, amount=request.amount)
    db.add(tx)
    db.commit()
    return {"detail": "Coins sent successfully"}

@app.get("/api/buy/{item}")
def buy_item(
    item: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = item.ToLower()
    if item not in MERCH_ITEMS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item not found")
    price = MERCH_ITEMS[item]
    if current_user.coins < price:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient coins")
    # Покупка мерча: списываем монеты и регистрируем покупку
    current_user.coins -= price
    purchase = models.Purchase(user_id=current_user.id, item=item, price=price)
    db.add(purchase)
    db.commit()
    return {"detail": f"Successfully purchased {item}"}
