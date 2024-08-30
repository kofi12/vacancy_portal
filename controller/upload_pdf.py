from fastapi import Depends, UploadFile
from sqlmodel import Session
from models.models import Document, Tenant
from database.db import get_session
import boto3

BUCKET_NAME = 'vacancy-portal'

def upload_f(file: UploadFile, object_name: str,
             db : Session = Depends(get_session)):

    #Upload file
    s3 = boto3.client('s3')
    s3.upload_fileobj(file, BUCKET_NAME, ExtraArgs={"ACL": "public-read"})


    #Store file url in Document table
    file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
    statement = ''

    pass