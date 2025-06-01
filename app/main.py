# main.py
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import User, Location
from app.schemas import UserCreate, UserResponse, LocationResponse
from app.auth import create_user, get_user_by_email, get_user_by_username
from typing import List

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="회원가입 API", version="1.0.0")

# API v1 라우터 생성
api_v1 = APIRouter(prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "회원가입 API 서버가 실행 중입니다."}

@api_v1.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """사용자 회원가입"""
    
    # 이메일 중복 검사
    existing_user_email = get_user_by_email(db, user.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )
    
    # 사용자명 중복 검사
    existing_user_username = get_user_by_username(db, user.username)
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다."
        )
    
    # 지역 ID 유효성 검사 (선택사항)
    if user.location_id is not None:
        location = db.query(Location).filter(Location.id == user.location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 지역입니다."
            )
    
    try:
        # 사용자 생성
        new_user = create_user(db, user)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 중 오류가 발생했습니다."
        )

@api_v1.get("/locations", response_model=List[LocationResponse])
async def get_locations(db: Session = Depends(get_db)):
    """모든 지역 조회"""
    locations = db.query(Location).all()
    return locations

@api_v1.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(name: str, db: Session = Depends(get_db)):
    """새 지역 생성"""
    location = Location(name=name)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

@api_v1.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 정보 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return user

# 라우터를 앱에 포함
app.include_router(api_v1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)