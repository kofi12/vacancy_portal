from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv('DB_URL', '')
engine = create_engine(DB_URL)

def get_session():
    with Session(engine) as session:
        yield session