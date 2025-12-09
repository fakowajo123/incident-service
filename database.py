# incident-service/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file (used for local Python script execution)
load_dotenv()

# --- Database Connection Configuration ---
# Construct the connection string using environment variables
DATABASE_URL = "postgresql+psycopg2://{user}:{password}@{host}/{name}".format(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    name=os.getenv("DB_NAME")
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Database Model (Incident) ---
class IncidentDB(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(Text)
    severity = Column(String(16))
    status = Column(String(16))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# Function to initialize the database (create tables)
def init_db():
    print("Attempting to create database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully or already exist.")

# If this file is run directly, initialize the DB (Used by Docker Compose)
if __name__ == "__main__":
    init_db()