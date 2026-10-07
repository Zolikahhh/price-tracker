from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.schemas import UserCreate, UserResponse
from src.core.security import get_password_hash, verify_password, create_access_token
from src.db.models import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Új felhasználó regisztrációja.
    """
    # Ellenőrizzük, hogy létezik-e már a megadott email
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ezzel az email címmel már regisztráltak."
        )

    # Hasheljük a jelszót és elmentjük a usert
    hashed_pwd = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        password_hash=hashed_pwd
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Bejelentkezés és JWT token igénylése (Swagger UI kompatibilis OAuth2 form).
    """
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Helytelen email cím vagy jelszó.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generálunk egy JWT access tokent
    access_token = create_access_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }