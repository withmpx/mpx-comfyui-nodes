import os
import sys
import torch

# MPX imports    
from .utils.general import hash_node_inputs, image_query_with_with_json_parsing
from .sdk.utils.image_helpers import convert_from_torch_to_PIL, convert_from_PIL_to_torch  

from ..base import BaseNode


def pick_best_image_from_four(generated_images, user_conditions, image_info, style_guide):
    num_images = len(generated_images)
    if num_images < 2 or num_images > 4:
        raise ValueError(f"Number of images must be between 2 and 4, got {num_images}")
        
    query = f"You are given {num_images} images."
    
    # Add context about what the images represent
    if image_info:
        query += f"\nThese images represent: {image_info}\n"
        query += "Consider this context when evaluating how well each image meets the conditions.\n"
    
    # Add style guidelines
    if style_guide:
        query += f"\nStyle Guidelines:\n{style_guide}\n"
        query += "Consider how well each image adheres to these style guidelines.\n"
    
    # Main task with enhanced evaluation criteria
    query += f"\nYour task is to select the best image based on these conditions:\n{user_conditions}\n\n"
    query += "Return your answer as a JSON with two keys:\n"
    query += f"1. 'image_index': A number from 1 to {num_images} indicating the best image\n"
    query += "2. 'reasoning': Explain your choice by:\n"
    query += "   - Describing why the chosen image is best\n"
    query += "   - Pointing out specific elements that match the conditions and those that do not\n"
    if image_info or style_guide:
        query += "   - Explaining how well it represents the intended context\n"
    if style_guide:
        query += "   - Evaluating how well it follows the style guidelines\n"
    query += "   - Explaining why other images were not selected"
    query += "\nNote: When picking the best image, info about the object and conditions are most important and any adherance to style guides are of a lower importance."

    parsed_results = image_query_with_with_json_parsing(query, generated_images)
    return parsed_results['image_index'], parsed_results['reasoning']


class Agent_PickBestImageFromList(BaseNode):
    """
    The Agent_PickBestImageFromList node analyzes a list of images and selects the best one based on user-defined conditions,
    with optional considerations for 3D model creation and style guidelines.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {
                    "default": [],
                    "tooltip": "The images to be considered.",
                    "agent_description": "List of images to analyze and select from."
                }),
                "user_conditions": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "The conditions to pick the best image.",
                    "tooltip": "The conditions to pick the best image.",
                    "agent_description": "Criteria for selecting the best image, such as specific visual elements, composition, or quality requirements."
                }),
                "used_for_3D": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Images are evaluated for creating 3D models.",
                    "agent_description": "When enabled, adds specific requirements to improve 3D model creation like full object view, centered composition, and proper lighting."
                }),
                "one_object_per_image": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Each image should only have one image in it. Useful for creating single 3D objects.",
                    "agent_description": "When enabled, enforces that each image contains exactly one object or character, which is useful since most 3D models should often contain only one object."
                }),
            },
            "optional": {
                "image_info": ("STRING", {
                    "default": "",
                    "defaultInput": True,
                    "placeholder": "Info about the image, such as the prompt used to generate it. (Recommended)",
                    "tooltip": "Info about the image, such as the prompt used to generate it. (Recommended)",
                    "agent_description": "Additional context about the images, such as generation prompts or intended purpose. Useful for improving image selection to match the image info."
                }),
                "style_guide": ("STRING", {
                    "default": "",
                    "defaultInput": True,
                    "placeholder": "Guidelines for the visual style and aesthetic qualities to consider.",
                    "tooltip": "Guidelines for the visual style and aesthetic qualities to consider.",
                    "agent_description": "Specific style requirements or aesthetic preferences to consider during image selection."
                }),
            }
        }
    

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("BestImage", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The selected best image that meets the specified conditions.",
        "Detailed explanation of why this image was chosen and how it meets the criteria."
    )

    def execute(self, images, user_conditions, used_for_3D, one_object_per_image, image_info="", style_guide=""):
        # Define the additional conditions text
        used_for_3D_condition = "Object must be in full view, centered and without any parts of the object cropped by the edge of the photo. Lighting is bright, diffuse, and indirect. Camera angle is a side view. Object must be on a completely blank white background."

        one_object_per_image_condition = "There must be only one object in the image. Never have more than one object or character."

        # If used_for_3D is checked, add the 3D optimization text to the user_conditions
        if used_for_3D:
            user_conditions = f"{user_conditions}\n\n{used_for_3D_condition}" if user_conditions else used_for_3D_condition
            
        # If one_object_per_image is checked, add the single object requirement to the user_conditions
        if one_object_per_image:
            user_conditions = f"{user_conditions}\n\n{one_object_per_image_condition}" if user_conditions else one_object_per_image_condition

        # first convert the tensors to a list of PIL images so they can be uploaded
        image_list = [] # PIL images

        tensor_shape = images.shape # (B x H x W x C) or (H x W x C)

        # we have a batch size so we should break this down into a regular list
        if len(tensor_shape) == 4:
            image_list = [convert_from_torch_to_PIL(i) for i in images]
            
        # assume no batch size so just process the one image
        elif len(tensor_shape) == 3:
            image_list.append(convert_from_torch_to_PIL(images))

        # If there's only one image, skip the API call and use that image
        if len(image_list) == 1:
            best_img_idx = 0
            reasoning = "Image 1 is selected because it is the only image"
        else:
            best_img_idx, reasoning = pick_best_image_from_four(image_list, user_conditions, image_info, style_guide)
            # agent returns index as a number between 1 to num_images, adjust it to be between 0 to num_images-1
            if best_img_idx in range(1, len(image_list) + 1): 
                best_img_idx -= 1
            else: 
                print(f"Returned index is NOT within range of [1 to {len(image_list)}]: {best_img_idx}", file=sys.stderr)

        print(f"Best Image Index: {best_img_idx}")
        print(f"Best Image Reasoning: {reasoning}")

        best_img = image_list[best_img_idx]

        torch_image = convert_from_PIL_to_torch(best_img)
        batch_tensor = torch.stack([torch_image], dim=0)
        return batch_tensor, reasoning
