import datetime as dt

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

print("befor db url")
# DATABASE_URL = "sqlite:///./appointments_db.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    print(f"Database URL found! Starts with: {db_url[:10]}...")
else:
    print("Database URL is MISSING from environment variables!")

engine = create_engine(DATABASE_URL) 
# , connect_args={"check_same_thread": False}
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, index=True)
    reason = Column(String, nullable=True)
    start_time = Column(DateTime, index = True)
    cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime, default = lambda: dt.datetime.now(dt.timezone.utc))

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# init_db()
