
from io import BytesIO
from copy import deepcopy
import requests
import torch
import numpy as np
from PIL import Image

### Data conversions

def convert_from_torch_to_PIL(img_torch: torch.Tensor) -> Image.Image:
    """
        Take a torch tensor whose pixel values range from (0.0 to 1.0) and 
        return a single PIL image which has pixels in range (0 to 255) and of type uint8
    """
    # use a deepcopy to avoid modifying the input tensor since we're removing the batch dimension
    img_tmp = deepcopy(img_torch)
    if img_torch.ndim == 4: # img_torch has dimensions: B x C x H x W
        img_tmp = img_tmp[0]  # use only the first image in the batch
    
    # permute dimensions if needed (C x H x W to H x W x C)
    if img_tmp.ndim == 3 and img_tmp.shape[0] == 3:
        img_tmp = img_tmp.permute(1, 2, 0)

    img_tmp = (img_tmp*255).clamp(0, 255).byte() # TODO: how to handle tensors that range beyond 0 to 1
    pil_image = Image.fromarray(img_tmp.numpy())
    return pil_image

def convert_from_PIL_to_torch(img_PIL: Image.Image):
    """
        Ensure pixels are in the range (0.0 to 1.0) otherwise image previews will not render properly.
    """
    return torch.from_numpy(np.array(img_PIL, dtype=np.float32) / 255.0) 

def convert_from_numpy_to_PIL(img_np: np.ndarray):
    return Image.fromarray(img_np)

def convert_from_numpy_to_torch(img_np: np.ndarray):
    return torch.from_numpy(img_np)

def convert_batch_tensor_to_tensor_list(batch_tensor: torch.Tensor):
    """ 
    Convert either:
      (B x H x W x C) tensor to a list of (H x W x C) tensors
      (H x W x C) tensor to a list with one element, the (H x W x C) tensor
    """
    tensor_list = []

    tensor_shape = batch_tensor.shape # (B x H x W x C) or (H x W x C)

    # we have a batch size so we should break this down into a regular list
    if len(tensor_shape) == 4:
        tensor_list = [i for i in batch_tensor]
        
    # assume no batch size so just process the one image
    elif len(tensor_shape) == 3:
        tensor_list.append(batch_tensor)

    return tensor_list


### Web downloads

def download_image_from_url_to_PIL(img_url: str):
    """
        Assume img_url is a valid URL to an image that can be accessed by this client.
    """
    img_downloaded = Image.open(BytesIO(requests.get(img_url).content))
    return img_downloaded

def download_image_from_url_to_torch(img_url: str):
    """
        Assume img_url is a valid URL to an image that can be accessed by this client.
        Return a torch image that ranges from 0 to 1.
    """
    img_downloaded = download_image_from_url_to_PIL(img_url)
    img_torch = convert_from_PIL_to_torch(img_downloaded)
    return img_torch
