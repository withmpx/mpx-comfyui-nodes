import os
import requests

def get_model_file_type_from_url(model_url: str) -> str:
    filename, file_ext = os.path.splitext(model_url)
    return file_ext[1:] # TODO: validate that the file extension is valid

def download_model_to_disk_from_url(model_url: str, folder: str, filename: str) -> str:
    """
    Detect the model type from the URL and download it to disk. Return the local filepath.
    """
    model_response = requests.get(model_url)
    model_type = get_model_file_type_from_url(model_url)
    fpath_model = f"{folder}/{filename}.{model_type.lower()}"
    with open(fpath_model, "wb") as model_file:
        model_file.write(model_response.content)
    return fpath_model
