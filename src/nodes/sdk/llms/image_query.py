import os
import requests
from io import BytesIO

from .constants import *

from ..sdk_client import get_client 
from ..get_status import get_status 

def image_query(query, images, **kwargs):
    return_image_urls = kwargs.get("return_image_urls", False)

    mpx_client = get_client()

    image_upload_headers = {
        'Authorization': f'Bearer {os.environ.get("MPX_SDK_BEARER_TOKEN")}',
        'Content-Type': 'image/png',
    }

    # upload all the given images 
    input_image_urls = []
    for img in images:

        # create asset ID for the image
        asset_id_response = mpx_client.assets.create(
            description="User uploaded image",
            name=f"image.png",
            type="image/png",
        )

        # convert the PIL image object into a standard PNG byte array to upload
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_byte_arr = img_byte_arr.getvalue()

        # actually upload the image
        # TODO: do error handling here for upload_response.status_code
        upload_response = requests.put(asset_id_response.asset_url, data=img_byte_arr, headers=image_upload_headers)

        # parse asset_url to obtain public url
        asset_url = asset_id_response.asset_url.split("?")[0]
        input_image_urls.append(asset_url)


    query_response = image_query_from_urls(query, input_image_urls, **kwargs)

    if return_image_urls: 
        return query_response, input_image_urls
    
    return query_response

def image_query_from_urls(query, images_urls, **kwargs):
    extra_params = {}
    extra_params["temperature"] = kwargs.get("temperature", DEFAULT_TEMPERATURE)
    extra_params["max_tokens"] = kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)

    mpx_client = get_client()
    image_query_request = mpx_client.llms.image_query(
        user_prompt=query,
        image_urls=images_urls,
        extra_body=extra_params
    )

    print(image_query_request)
    image_query_response = get_status(image_query_request.request_id)
    print(image_query_response)

    # TODO: do retry attempts if it status == failed
    return image_query_response.outputs.output
