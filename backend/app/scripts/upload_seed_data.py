from pathlib import Path

from app.services.blob_storage import AzureBlobService

storage = AzureBlobService()

BASE = Path(__file__).resolve().parents[3] / "examples"

DATA_DIR = BASE / "data"
POLICY_DIR = BASE / "policies"
PROMPT_DIR = BASE / "prompts"


def upload_directory(directory, container):
    for file in directory.glob("*"):
        if file.is_file():
            print(f"Uploading {file.name} -> {container}")

            storage.upload_file(
                container=container,
                file_path=str(file),
                blob_name=file.name
            )


upload_directory(DATA_DIR, "documents")
upload_directory(POLICY_DIR, "policies")
upload_directory(PROMPT_DIR, "prompts")

print("All files uploaded successfully.")
