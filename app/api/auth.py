from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.crud import get_user_by_email
from app.core.security import verify_password
from app.core.jwt import create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/token", summary="Login and get JWT token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # 1. Ищем пользователя по email (в OAuth2form поле username используется для email)
    user = await get_user_by_email(db, email=form_data.username)
    
    # 2. Проверяем, существует ли пользователь и правильный ли пароль
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Генерируем JWT-токен, зашивая внутрь email пользователя
    access_token = create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token, "token_type": "bearer"}