# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.database.user import async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
import csv, io
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/solvv/admin",
    tags=["users"]
)

# Dependency to get async DB session
async def get_session():
    async with async_session() as session:
        yield session

@router.get("/users/all", response_model=list[UserOut])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    """
    Get all users in the database.
    Always returns a list (empty if no users exist).
    """
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users

# Get all users or search by name
@router.get("/users", response_model=list[UserOut])
async def get_users(name: str = None, session: AsyncSession = Depends(get_session)):
    query = select(User)
    if name:
        query = select(User).where(
            or_(
                User.first_name.ilike(f"%{name}%"),
                User.last_name.ilike(f"%{name}%")
            )
        )
    result = await session.execute(query)
    users = result.scalars().all()
    
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    
    return users


# Add single user
@router.post("/user", response_model=UserOut)
async def add_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    new_user = User(**user.dict())
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

# Add users through CSV
@router.post("/user/csv")
async def add_users_csv(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode()))
    users_list = []
    for row in csv_reader:
        user = User(
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone_number=row["phone_number"]
        )
        session.add(user)
        users_list.append(user)
    await session.commit()
    return {"added": len(users_list)}

# Update user
@router.put("/user/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user: UserUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.user_id == user_id))
    existing_user = result.scalars().first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict(exclude_unset=True).items():
        setattr(existing_user, key, value)
    await session.commit()
    await session.refresh(existing_user)
    return existing_user

# Delete user
@router.delete("/user/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"detail": "User deleted successfully"}
