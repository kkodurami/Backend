# main.py
import os
import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.models import User, Location
from app.schemas import UserCreate, UserResponse, LocationResponse
from app.auth import create_user, get_user_by_email, get_user_by_username

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from app.auth import verify_password, get_user_by_email  # 기존 함수 활용

# 템플릿 디렉토리 설정 (플랫폼 독립적 경로)
templates = Jinja2Templates(directory=os.path.join("app", "templates"))

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="회원가입 API", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "kkodurmi main page"}


@app.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    """회원가입 폼 페이지"""
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup", response_class=HTMLResponse)
async def register_user_from_form(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    location_id_raw: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # location_id 처리 (빈 문자열 또는 None -> None)
    location_id = None
    if location_id_raw:
        try:
            location_id = int(location_id_raw)
        except ValueError:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "지역 ID는 숫자여야 합니다."},
                status_code=400,
            )

    # 이메일 중복 검사
    if get_user_by_email(db, email):
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "이미 등록된 이메일입니다."},
            status_code=400,
        )

    # 사용자명 중복 검사
    if get_user_by_username(db, username):
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "이미 사용 중인 사용자명입니다."},
            status_code=400,
        )

    # 지역 ID 유효성 검사
    if location_id is not None:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "존재하지 않는 지역입니다."},
                status_code=400,
            )

    try:
        user_data = UserCreate(
            email=email,
            username=username,
            password=password,
            location_id=location_id,
        )
        create_user(db, user_data)
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "message": "회원가입이 완료되었습니다!"},
        )
    except Exception as e:
        logging.error(f"사용자 생성 중 오류: {e}", exc_info=True)
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "사용자 생성 중 오류가 발생했습니다."},
            status_code=500,
        )


@app.get("/locations", response_model=List[LocationResponse])
async def get_locations(db: Session = Depends(get_db)):
    """모든 지역 조회"""
    return db.query(Location).all()


@app.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(name: str, db: Session = Depends(get_db)):
    """새 지역 생성"""
    location = Location(name=name)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 정보 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )
    return user

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """로그인 폼 페이지"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "이메일 또는 비밀번호가 올바르지 않습니다."},
            status_code=400,
        )

    # 로그인 성공 → 예시로는 메세지 출력만
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "message": f"{user.username}님 환영합니다!"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
