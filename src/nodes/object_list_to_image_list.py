import os
import datetime
import torch

from joblib import Parallel, delayed, cpu_count

import comfy.utils

from folder_paths import get_output_directory


# MPX imports
from .sdk.components.text_to_image import component_text_to_image
from .sdk.utils.image_helpers import download_image_from_url_to_PIL, convert_from_PIL_to_torch

from ..base import BaseNode


class ObjectListToImageList(BaseNode):
    """
    The ObjectListToImageList node converts a list of objects into a list of images. Returns images.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "object_list": ("LIST", {
                    "tooltip": "List of object descriptions to generate images from. Each description should be detailed and clear.",
                    "agent_description": "A list of objects to be converted into images."
                }),
            },
            "optional":
            {
                "output_folder": ("STRING", {
                    "default": get_output_directory(),
                    "placeholder": "Directory where generated images will be saved. Defaults to ComfyUI's output directory.",
                    "tooltip": "Directory where generated images will be saved. Defaults to ComfyUI's output directory.",
                    "agent_description": "The folder where the images will be saved. Default: system output directory."
                }),
                "num_processes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": cpu_count(),
                    "tooltip": "Number of parallel processes to use for image generation",
                    "agent_description": "Number of parallel processes. Default: 1."
                }),
                "seed": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "tooltip": "Random seed for reproducible results. Manually set to 'fixed' to ensure the seed does not change.",
                }),
                "used_for_3D": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "When enabled, optimizes image for good 3D models generation",
                    "agent_description": "Images are optimized for creating 3D models. Default: true."
                }),
                "only_one_object_per_desc": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "When enabled, ensures each generated image contains only one object, which is ideal for creating individual 3D models.",
                    "agent_description": "Each description in the object list has only one object in it. Useful for creating single 3D objects. Default: true."
                })
            }
        }

    RETURN_TYPES = ("IMAGE", )
    RETURN_NAMES = ("GeneratedObjects_images",)
    RETURN_AGENT_DESCRIPTIONS = (
        "Generated images from the input object list.",
    )

    def execute(self, object_list, output_folder, num_processes, seed, used_for_3D=True, only_one_object_per_desc=True):

        if os.path.exists(output_folder) == False:
            print(f"Output folder: {output_folder} DOES NOT EXIST!")
            output_folder = get_output_directory()
            print(f"Defaulting to: {output_folder}")

        global num_images_processed
        num_images_processed = 0

        def generate_image_from_object_description(obj_desrc: str, seed_val: int, obj_idx: int, n_objs: int, progress_bar: comfy.utils.ProgressBar):
            """
            Generate an image for one object description.
            """
            global num_images_processed

            print(f"Processing [{obj_idx}/{n_objs}] => {obj_desrc}")

            desired_n_images = 1 # TODO: determine how to handle multiple images per object

            # Build the prompt based on parameters
            prompt = f"wbgmsst. {obj_desrc}"
            
            # If used_for_3D is checked, add the 3D optimization text to the prompt
            if used_for_3D:
                prompt += "\n\nObject must be in full view, centered and without any parts of the object cropped by the edge of the photo. Lighting is bright, diffuse, and indirect. Camera angle is a side view. Object must be on a completely blank white background."
            
            # If only_one_object is checked, add the single object requirement to the prompt
            if only_one_object_per_desc:
                prompt += "\n\nThere must be only one object in the image. Never have more than one object or character. Do not show walls or floor if not specified above."
            
            image_urls, request_id = component_text_to_image(
                prompt=prompt,
                num_images=desired_n_images,
                seed=seed_val,
                lora_scale=0.8,
                lora_weights="https://huggingface.co/gokaygokay/Flux-Game-Assets-LoRA-v2"
            )

            # download results and save to disk if an output folder is given
            PIL_img = download_image_from_url_to_PIL(image_urls[0])
            torch_img = convert_from_PIL_to_torch(PIL_img)

            if output_folder: 
                str_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                PIL_img.save(f"{output_folder}/object_to_image_{str_timestamp}.png")

            # update the comfy progress bar if one is given
            if progress_bar is not None:
                num_images_processed += 1
                progress_bar.update_absolute(num_images_processed, n_objs, ("PNG", PIL_img, None))
            
            return torch_img


        n_objects = len(object_list)
        pbar = comfy.utils.ProgressBar(n_objects)

        image_tensors = []

        if num_processes == 1:
            for i in range(n_objects):
                img_tensor = generate_image_from_object_description(object_list[i],
                                                                    seed,
                                                                    i,
                                                                    n_objects,
                                                                    pbar)
                image_tensors.append(img_tensor)

        else:
            image_tensors = Parallel(backend="threading", n_jobs=num_processes)(delayed(generate_image_from_object_description)(
                object_list[i], 
                seed,
                i, 
                n_objects,
                pbar
            ) for i in range(n_objects))

        batch_tensor = torch.stack(image_tensors, dim=0)
        return (batch_tensor, )
