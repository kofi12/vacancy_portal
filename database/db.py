from sqlmodel import create_engine, Session # type: ignore
from dotenv import load_dotenv # type: ignore
import os

DB_URL = os.getenv('DB_URL', '')
engine = create_engine(DB_URL)

def get_session():
    with Session(engine) as session:
        yield session