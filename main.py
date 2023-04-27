from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List
from datetime import datetime
import enum
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware


# Database configuration
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enum for user types
class UserType(enum.Enum):
    doctor = 'doctor'
    substitute_doctor = 'substitute_doctor'

# Database models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String)
    user_type = Column(Enum(UserType))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = relationship("User", back_populates="schedules")

User.schedules = relationship("Schedule", back_populates="doctor", cascade="all, delete")

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: str
    user_type: UserType

class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone_number: str
    user_type: UserType

    class Config:
        orm_mode = True

class ScheduleCreate(BaseModel):
    start_date: datetime
    end_date: datetime
    status: str

class ScheduleOut(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime
    status: str
    doctor: UserOut

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    sender: UserOut
    receiver: UserOut
    content: str

    class Config:
        orm_mode = True


# Database models
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    substitute_doctor_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedule = relationship("Schedule")
    substitute_doctor = relationship("User")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

# Additional Pydantic models
class ApplicationCreate(BaseModel):
    schedule_id: int
    substitute_doctor_id: int
    status: str

class ApplicationOut(BaseModel):
    id: int
    schedule: ScheduleOut
    substitute_doctor: UserOut
    status: str

    class Config:
        orm_mode = True

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token settings (replace with your own secret key)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to hash password
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Function to verify password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Function to authenticate user
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

# Function to create access token
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# FastAPI app
app = FastAPI()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db_user.password = get_password_hash(db_user.password)  # Hash the user's password
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Login endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users", response_model=List[UserOut])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/schedules", response_model=List[ScheduleOut])
def get_schedules(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).all()
    return schedules

@app.post("/schedules", response_model=ScheduleOut)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@app.get("/schedules/{schedule_id}", response_model=ScheduleOut)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule



# Applications endpoints
@app.post("/applications", response_model=ApplicationOut)
def create_application(application: ApplicationCreate, db: Session = Depends(get_db)):
    db_application = Application(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

@app.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

# Messaging endpoints
@app.post("/messages", response_model=MessageOut)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@app.get("/messages/{user_id}", response_model=List[MessageOut])
def get_messages(user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter((Message.sender_id == user_id) | (Message.receiver_id == user_id)).all()
    return messages
