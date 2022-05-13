from googleStorage import CLOUD_STORAGE_BUCKET
from google.cloud import storage

container_name = "bookphotos"


gcs = storage.Client()
bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
