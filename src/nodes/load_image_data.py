import os 
from io import BytesIO
import requests
from PIL import Image
import torch
import zipfile
import tempfile
from urllib.parse import urlparse

from .sdk.utils.image_helpers import convert_from_PIL_to_torch, download_image_from_url_to_PIL

from ..base import BaseNode


class LoadImageData(BaseNode):
    """
    The LoadImageData node loads image data from various sources including local files, folders, URLs, and archives.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_location": ("STRING", {
                    "default": "",
                    "placeholder": "Path to image file, image folder, or URL to a remote image. Supports jpg, jpeg, png, webp, and bmp",
                    "tooltip": "Path to image file, image folder, or URL to a remote image. Supports jpg, jpeg, png, webp, and bmp",
                    "agent_description": "The location of the one or more images to load - can be a file path, folder path, or URL. Supports jpg, jpeg, png, webp, and bmp formats."
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", )
    RETURN_NAMES = ("Images", )
    RETURN_AGENT_DESCRIPTIONS = (
        "The loaded image or images as a tensor or batch of tensors.",
    )
    OUTPUT_NODE = True
    
    
    SUPPORTED_IMAGE_FILE_FORMATS = (".jpg", ".jpeg", ".png", ".webp", '.bmp')
    SUPPORTED_TEXT_FILE_FORMATS = (".txt", ".md")
    SUPPORTED_COMPRESSED_FILE_FORMATS = (".zip")

    def execute(self, input_location: str):

        loaded_data = None
        
        # input_location exists on our local disk
        if os.path.exists(input_location):
            loaded_data = self.__load_local_disk_data(input_location)
            
        # input_location does not exist on local disk? check if it's a URL to a location
        else:
            loaded_data = self.__load_remote_data(input_location)

        return loaded_data


    def __load_local_disk_data(self, input_location: str) -> list[torch.Tensor]:
        loaded_data = []

        # we have a folder, list all top-level files and load only the images
        if os.path.isdir(input_location):
            loaded_data = self.__load_image_data_from_folder(input_location)

        # it's a regular old file, handle all the different cases
        elif os.path.isfile(input_location):

            # we have a text file - read it and assume each line is potetionally a filepath to an image
            if input_location.lower().endswith(LoadImageData.SUPPORTED_TEXT_FILE_FORMATS):
                loaded_data = self.__load_image_data_from_filepaths_in_text_file(input_location)

            # we have a zip file - unzip to a temp location and then load it from a folder
            elif input_location.lower().endswith(LoadImageData.SUPPORTED_COMPRESSED_FILE_FORMATS):
                zf = zipfile.ZipFile(input_location)
                with tempfile.TemporaryDirectory() as tempdir:
                    zf.extractall(tempdir)
                    loaded_data = self.__load_image_data_from_folder(tempdir)

        # this should not happen as this means the input_location not a folder or a file
        else:
            raise ValueError(f"[ {input_location} ] does not point to a folder or a specific file!")

        # we gots some image data? return it as a batched Tensor
        if len(loaded_data) > 0:
            return [torch.stack(loaded_data, dim=0)]


    def __load_remote_data(self, input_location: str) -> list[torch.Tensor]:
        loaded_data = []

        # we have a properly formatted URL
        if self.__is_valid_url(input_location):

            # we have a URL to a specific image file, download and load it
            if input_location.lower().endswith(LoadImageData.SUPPORTED_IMAGE_FILE_FORMATS):
                PIL_image = download_image_from_url_to_PIL(input_location)
                img_torch = convert_from_PIL_to_torch(PIL_image)
                loaded_data.append(img_torch)

            # we have a URL to some zip file, download it to a temp location on disk and then load it like a folder
            elif input_location.lower().endswith(LoadImageData.SUPPORTED_COMPRESSED_FILE_FORMATS):
                response = requests.get(input_location)
                response.raise_for_status()
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                        zip_ref.extractall(tmp_dir)
                        loaded_data = self.__load_image_data_from_folder(tmp_dir)

            else:
                raise ValueError(f"Unable to load remote data located @ [ {input_location}] ")

        else:
            raise ValueError(f"[ {input_location} ] is not a valid URL!")


        if len(loaded_data) > 0:
            return [torch.stack(loaded_data, dim=0)]


    def __load_image_data_from_folder(self, folder: str) -> list[torch.Tensor]:
        loaded_data = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                fullpath = os.path.join(root, file).strip()
                img_data = self.__load_image_data_from_filepath(fullpath)
                if img_data is not None: loaded_data.append(img_data)
        return loaded_data

    def __load_image_data_from_filepaths_in_text_file(self, text_filepath: str) -> list[torch.Tensor]:
        loaded_data = []
        with open(text_filepath, "r") as file:
            text_data = file.readlines()
            for td in text_data:
                img_data = self.__load_image_data_from_filepath(td.strip())
                if img_data is not None: loaded_data.append(img_data)
        return loaded_data

    def __load_image_data_from_filepath(self, filepath_to_image: str) -> torch.Tensor | None:
        """
        Given a path to an image file on disk, attempt to load it and return as a torch.Tensor.
        Return None otherwise.
        """
        if filepath_to_image.lower().endswith(LoadImageData.SUPPORTED_IMAGE_FILE_FORMATS):
            try:
                PIL_image = Image.open(filepath_to_image)
                img_torch = convert_from_PIL_to_torch(PIL_image)
                return img_torch
            except Exception as e:
                print(f"Error loading [ {filepath_to_image} ]. Skipping. Error details: {e}")
        else:
            print(f"Unsupported file formath for image at [ {filepath_to_image} ]. Skipping.")


    def __is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            # A valid URL should have at least a scheme and netloc.
            return all([result.scheme, result.netloc])
        except Exception:
            return False