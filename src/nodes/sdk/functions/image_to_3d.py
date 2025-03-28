import os
from io import BytesIO
import requests
from urllib.parse import urlparse

import torch
from PIL import Image

from ..sdk_client import get_client 
from ..get_status import get_status 

from ..utils.image_helpers import convert_from_torch_to_PIL


def function_image_to_3d(image: Image.Image | torch.Tensor | str, 
                         image_description: str = "User uploaded image.",
                         seed: int = 1,
                         texture_size: int = 1024) -> dict:
    """
        Given some representation of an image, run the imageto3d function via the MPX API.

        image can one of the following:
            1) a single PIL image which will be uploaded to the MPX servers for processing
            2) a filepath to an image which will be loaded from disk and then turned into a single PIL in which (1) will then apply
            3) a url which can then be passed to the function directly
    """

    image_data = None

    if isinstance(image, Image.Image):
        image_data = image

    elif isinstance(image, torch.Tensor):
        image_data = convert_from_torch_to_PIL(image)

    # need to determine if it's a valid filepath on disk or a URL
    # return errors for invalid URLs and/or non-existent filepaths
    elif isinstance(image, str):

        # we got a filepath on disk, load it up
        if os.path.exists(image):
            image_data = Image.open(image)


    # we got some valid image data either directly or by loading an image from disk
    if image_data is not None:
        return _function_imageto3d__PIL_image(image_data, image_description, seed, texture_size)
    
    # image_data is None means we weren't given a PIL image nor a path to an image on disk
    # if we have a URL then we can pass that to the API instead
    elif __is_valid_url(image):
        
        # make sure the url has an image file at the end
        # NOTE: no actual validation of the data is done
        vals = image.split("/")
        img_filename = vals[-1]
        filename, file_ext = os.path.splitext(img_filename)

        if file_ext.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]:
            return _function_imageto3d__image_url(image, seed, texture_size)
        else:
            raise ValueError(f"Unsupported image file extension: {file_ext}")

    else:
        raise ValueError("Input parameter 'image' is not a PIL.Image, a path to an image on disk or a URL to an image.")


def _function_imageto3d__PIL_image(image: Image.Image, 
                                   image_description: str = "User uploaded image",
                                   seed: int = 1,
                                   texture_size: int = 1024) -> dict:
    """
        Upload the given image and run the imageto3d function.
    """
    mpx_client = get_client()
    
    image_upload_headers = {
        'Authorization': f'Bearer {os.environ.get("MPX_SDK_BEARER_TOKEN")}',
        'Content-Type': 'image/png',
    }

    # create asset ID for the image
    asset_resp = mpx_client.assets.create(
        description=image_description,
        name=f"image.png",
        type="image/png",
    )

    # convert the PIL image object into a standard PNG byte array to upload
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    img_byte_arr = img_byte_arr.getvalue()

    # actually upload the image
    # TODO: do error handling here for upload_response.status_code
    upload_response = requests.put(asset_resp.asset_url, data=img_byte_arr, headers=image_upload_headers)

    # call imageto3d endpoint with the image asset ID
    imageto3d_resp = mpx_client.functions.imageto3d(
        image_request_id = asset_resp.request_id,
        seed=seed,
        texture_size=texture_size
    )
    print(f'[mpx_sdk] imageto3d.request_id: {imageto3d_resp.request_id}')

    # wait for the endpoint to complete
    endpoint_response = get_status(imageto3d_resp.request_id)

    print(f'[mpx_sdk] imageto3d.status_response: {endpoint_response}')

    if endpoint_response.status != 'complete':
        raise ValueError(f'imageto3d request failed with status: {endpoint_response.status}')
  
    # return a dict with the URLs and the request_id
    ret_data = {}
    ret_data["glb_url"] = endpoint_response.outputs.glb
    ret_data["fbx_url"] = endpoint_response.outputs.fbx
    ret_data["usdz_url"] = endpoint_response.outputs.usdz
    ret_data["thumbnail_url"] = endpoint_response.outputs.thumbnail
    ret_data["request_id"] = imageto3d_resp.request_id
    return ret_data


def _function_imageto3d__image_url(image_url: str, 
                                   seed: int = 1,
                                   texture_size: int = 1024) -> dict:
    """
        Use an image URL as the input to the imageto3d endpoint.
    """
    mpx_client = get_client()

    # use request_id as image source
    imageto3d_resp = mpx_client.functions.imageto3d(
        image_url=image_url,
        seed=seed,
        texture_size=texture_size,
    )
    print(imageto3d_resp)
    imageto3d_request_id = imageto3d_resp.request_id
    print(f'mesh genrequest_id: {imageto3d_request_id}')

    # wait for the request to complete
    imageto3d_response = get_status(imageto3d_request_id)
    print(f'status_response: {imageto3d_response}')

    if imageto3d_response.status != 'complete':
        raise ValueError(f'imageto3d request failed with status: {imageto3d_response.status}')
  
    # Retrieve the generated 3D object urls



def __is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        # A valid URL should have at least a scheme and netloc.
        return all([result.scheme, result.netloc])
    except Exception:
        return False





