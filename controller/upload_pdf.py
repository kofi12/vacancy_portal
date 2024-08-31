from fastapi import Depends, UploadFile
from sqlmodel import Session
from models.models import Document, Tenant
from database.db import get_session
import boto3

BUCKET_NAME = 'vacancy-portal'
AWS_REGION = 'us-east-2'

def upload_f(file: UploadFile, tenant_id: int,
             db : Session = Depends(get_session)):

    print('Hitting endpiont')
    print(file)
    print(file.content_type)
    #Upload file
    s3 = boto3.client('s3')
    s3.upload_fileobj(file.file,
                      BUCKET_NAME,
                      file.filename)

    #Store file url in Document table
    file_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file.filename}"
    document = Document(file_name=file.filename,
                        url=file_url,
                        tenant_id=tenant_id)

    db.add(document)
    db.commit()
    return document