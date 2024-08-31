from fastapi import Depends, HTTPException, UploadFile, status
from sqlmodel import Session, select
from models.models import Document, Tenant
from models.schemas import DocumentDown
from database.db import get_session
import boto3

BUCKET_NAME = 'vacancy-portal'
AWS_REGION = 'us-east-2'

def download_f(id: int, db: Session = Depends(get_session)):
    statement = select(Document).where(Document.id == id)
    try:
        doc = db.exec(statement).first()
    except:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Document does not exist')

    key = doc.url # type: ignore
    filename = doc.file_name # type: ignore

    s3 = boto3.client('s3')
    return s3.download_file(BUCKET_NAME, filename, filename)
