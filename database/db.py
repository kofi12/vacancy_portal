from sqlmodel import create_engine, Session # type: ignore
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()

DB_URL = os.getenv('DATABASE_URL', '')
engine = create_engine(DB_URL)

def get_session():
    with Session(engine) as session:
        yield session