from azure.storage.blob import BlobServiceClient
import os


class AzureBlobService:
    def __init__(self):
        self.connection_string = os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING"
        )

        if not self.connection_string:
            raise ValueError(
                "AZURE_STORAGE_CONNECTION_STRING not set"
            )

        self.client = BlobServiceClient.from_connection_string(
            self.connection_string
        )

    def upload_file(
        self,
        container: str,
        file_path: str,
        blob_name: str
    ):
        container_client = self.client.get_container_client(
            container
        )

        with open(file_path, "rb") as data:
            container_client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True
            )

    def download_blob(
        self,
        container: str,
        blob_name: str,
        download_path: str
    ):
        blob_client = self.client.get_blob_client(
            container=container,
            blob=blob_name
        )

        with open(download_path, "wb") as file:
            file.write(
                blob_client.download_blob().readall()
            )

    def list_blobs(
        self,
        container: str
    ):
        container_client = self.client.get_container_client(
            container
        )

        return [
            blob.name
            for blob in container_client.list_blobs()
        ]
