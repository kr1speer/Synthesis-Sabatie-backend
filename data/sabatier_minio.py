import json
import os
import uuid

from minio import Minio

SABATIER_MINIO_ENDPOINT = os.getenv("SABATIER_MINIO_ENDPOINT", "localhost:9000")
SABATIER_MINIO_BUCKET = os.getenv("SABATIER_MINIO_BUCKET", "sabatie-assets")
SABATIER_MINIO_ACCESS_KEY = os.getenv("SABATIER_MINIO_ACCESS_KEY", "root")
SABATIER_MINIO_SECRET_KEY = os.getenv("SABATIER_MINIO_SECRET_KEY", "rootpassword")

minio_client = Minio(
    SABATIER_MINIO_ENDPOINT,
    access_key=SABATIER_MINIO_ACCESS_KEY,
    secret_key=SABATIER_MINIO_SECRET_KEY,
    secure=False,
)

PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{SABATIER_MINIO_BUCKET}/*"],
        }
    ],
}


def ensure_material_bucket() -> None:
    if not minio_client.bucket_exists(SABATIER_MINIO_BUCKET):
        minio_client.make_bucket(SABATIER_MINIO_BUCKET)
    minio_client.set_bucket_policy(SABATIER_MINIO_BUCKET, json.dumps(PUBLIC_READ_POLICY))


def upload_material_file(upload_file) -> str:
    extension = os.path.splitext(upload_file.filename or "")[1].lower()
    object_name = f"{uuid.uuid4().hex}{extension}"

    minio_client.put_object(
        SABATIER_MINIO_BUCKET,
        object_name,
        upload_file.file,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=upload_file.content_type or "application/octet-stream",
    )
    return object_name


def remove_material_file(object_name: str) -> None:
    minio_client.remove_object(SABATIER_MINIO_BUCKET, object_name)
