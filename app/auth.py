# auth.py
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserCreate

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """비밀번호를 해시화"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """사용자명으로 사용자 조회"""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    """새 사용자 생성"""
    # 비밀번호 해시화
    hashed_password = hash_password(user.password)
    
    # 사용자 객체 생성
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        location_id=user.location_id
    )
    
    # 데이터베이스에 저장
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user