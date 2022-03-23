from azure.storage.blob import BlobServiceClient
import os

connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(
    conn_str=connect_str)
