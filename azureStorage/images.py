from azureStorage import blob_service_client

container_name = "bookphotos"

try:
    container_client = blob_service_client.get_container_client(
        container=container_name)
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container(container_name)
