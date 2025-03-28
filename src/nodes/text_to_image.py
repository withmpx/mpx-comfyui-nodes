import torch

from .sdk.components.text_to_image import component_text_to_image
from .sdk.utils.image_helpers import download_image_from_url_to_PIL, convert_from_PIL_to_torch

from ..base import BaseNode

class TextToImage(BaseNode):
    """
    The Text2Image node generates images from text prompts. Returns generated images in various formats.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Text description of the image you want to generate",
                    "tooltip": "Text description of the image you want to generate",
                    "agent_description": "The text prompt to generate images from."
                }),
                "num_images": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "tooltip": "Number of images to generate (1-4)",
                    "agent_description": "Number of images to generate. Range: 1-4, default: 1."
                }),
                "seed": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "tooltip": "Random seed for reproducible results. Manually set to 'fixed' to ensure the seed does not change.",
                    "agent_description": "Random seed for reproducible results. Range: 1-1000000, default: 1."
                }),
                "used_for_3D": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Images are optimized for creating 3D models.",
                    "agent_description": "Images are optimized for creating 3D models. Default: true."
                }),
                "only_one_object": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "The description has only one object in it. Useful for creating single 3D objects.",
                    "agent_description": "The description has only one object in it. Useful for creating single 3D objects. Default: true."
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "LIST", "STRING")
    RETURN_NAMES = ("Images", "ImageUrls_list", "RequestID_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "Generated image tensors.",
        "URLs to the generated images.",
        "The request ID corresponding to the image generation call."
    )
    OUTPUT_NODE = True
    
    def execute(self, prompt, num_images, seed, used_for_3D, only_one_object):
        # If used_for_3D is checked, add the 3D optimization text to the prompt
        if used_for_3D:
            # Add newlines between the original prompt and the 3D optimization text
            prompt = f"{prompt}\n\nObject must be in full view, centered and without any parts of the object cropped by the edge of the photo. Lighting is bright, diffuse, and indirect. Camera angle is a side view. Object must be on a completely blank white background."
            
        # If only_one_object is checked, add the single object requirement to the prompt
        if only_one_object:
            prompt = f"{prompt}\n\nThere must be only one object in the image. Never have more than one object or character. Do not show walls or floor if not specified above."
            

        # TODO: find a set of loras which work really well before re-introducing these two parameters
        default_lora_scale = 0.8
        default_lora_weights = "https://huggingface.co/gokaygokay/Flux-Game-Assets-LoRA-v2"

        image_urls, request_id = component_text_to_image(prompt, num_images, seed, default_lora_scale, default_lora_weights)
        print(f"image_urls: {image_urls}")
        image_tensors = []
        for img_url in image_urls:
            PIL_image = download_image_from_url_to_PIL(img_url)
            torch_image = convert_from_PIL_to_torch(PIL_image)
            image_tensors.append(torch_image)
            
        batch_tensor = torch.stack(image_tensors, dim=0)
        return (batch_tensor, image_urls, request_id)

