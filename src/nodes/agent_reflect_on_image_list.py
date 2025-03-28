# system imports
import os
import datetime
import torch

from joblib import Parallel, delayed, cpu_count


# comfy imports
from folder_paths import get_output_directory
import comfy.utils

# MPX imports
from .sdk.llms.call import llm_call
from .sdk.llms.image_query import image_query
from .utils.general import hash_node_inputs, parse_llm_json, variable_substitution

from .sdk.components.text_to_image import component_text_to_image
from .sdk.utils.image_helpers import convert_from_torch_to_PIL, convert_from_PIL_to_torch, convert_batch_tensor_to_tensor_list, download_image_from_url_to_PIL

from ..base import BaseNode


def convert_checklist_results_to_list_of_issues(checklist_results):
    """
    checklist_results = four bools
        item1_checked = item01_object_is_centered_and_fully_visible(input_image)
        item2_checked = item02_image_has_only_one_object(input_image, input_obj_descr)
        item3_checked = item03_adheres_to_style_guide(input_image, input_style_guide)
        item4_checked = item04_has_blank_white_background(input_image)
    """
    ret = ""
    n_item = 1
    if checklist_results[0] == False: 
        ret += f"({n_item}) The object is not centered and/or fully visible. There are elements of it that is cut off.\n"
        n_item += 1
    if checklist_results[1] == False: 
        ret += f"({n_item}) There are multiple objects present.\n"
        n_item += 1
    if checklist_results[2] == False: 
        ret += f"({n_item}) Does not adhere to the custom user rules.\n"
        n_item += 1
    if checklist_results[3] == False: 
        ret += f"({n_item}) The background is not blank and white.\n"
        n_item += 1
    return ret

def run_prompt_transform(old_prompt, checklist_results, original_theme, custom_user_directions):
    llm_params = {}
    llm_params["temperature"] = 0

    extra_params = {}
    extra_params["model"] = "gpt-4o"

    sys_prompt = "You are a natural language expert who is specialized with creating new text prompts from existing text prompts. Your job is to take: (1) an existing user provided prompt, (2) a list of issues which detail what is wrong with it, (3) the original theme of the prompt, (4) some custom user directions and then produce a new prompt that addresses the list of issues as well as adhering to both the original theme of the prompt and the given custom user direcitons. It might be that the original theme and the custom user directions are in conflict with each other. In those cases do your base to balance the two.\n\n"
    sys_prompt += "Return the answer as only a JSON with a two keys 'new_prompt' and 'reasoning'. In the 'new_prompt' key provide an updated prompt with no premable or explanation. Ensure to address all of the issues that are given to you and that you've done your best to balance between the original theme and the custom user directions. In the 'reasoning' key provide an explanation for why the new prompt makes sense, addressses all of the given issues and also follows both the original theme and the custom user directions. Just the JSON only is returned.\n\n"

    human_prompt = "### (1) Existing user provided prompt:\n{old_prompt}\n\n"
    human_prompt += "### (2) List of issues with the original prompt:\n{list_of_issues}\n\n"
    human_prompt += "### (3) Original theme of the prompt:\n\n{original_theme}\n\n"
    human_prompt += "### (4) Custom User Directions:\n\n{custom_user_directions}\n\n"


    prompt_data = {}
    prompt_data["old_prompt"] = old_prompt
    prompt_data["list_of_issues"] = convert_checklist_results_to_list_of_issues(checklist_results)
    prompt_data["original_theme"] = original_theme
    prompt_data["custom_user_directions"] = custom_user_directions

    sys_prompt = variable_substitution(sys_prompt, prompt_data)
    human_prompt = variable_substitution(human_prompt, prompt_data)

    llm_response = llm_call(sys_prompt, human_prompt, llm_params, extra_params)
    parsed_response = parse_llm_json(llm_response)

    print("invoke_unit__prompt_transform():")
    print(f"old_prompt = '{old_prompt}'")
    print(parsed_response)

    return parsed_response['new_prompt'], parsed_response['reasoning']

def run_through_check_list_compressed(input_image, input_obj_descr, input_user_directions):
    main_query = "You are an expert at inspecting images for defects. You are given an image and you need to answer the following questions:\n"
    main_query += "(1) Is the main object fully visible (no portion is cut-off) and centered in the given image?\n"
    main_query += f"(2) Here is a detailed description of the given image: {input_obj_descr}. Ignoring all the extra descriptions, is there only one main object in the given image?\n"
    main_query += "(3) Does the given image have a blank white background?\n"
    main_query += f"(4) Here are custom user directions that the given image should adhere to: {input_user_directions}. Does the given image really adhere to the given custom user directions? Be critical.\n"

    main_query += "\n"

    # main_query += "Return the answers as only a JSON with a two keys 'answers' and 'reasoning'.\n"
    # main_query += "In the 'answers' key provide the answer as list consisting of 'yes' and 'no' by thinking things through in a step-by-step fashion. Ensure that no premable or explanation is included. Recall you need to answer questions (1) to (4) so this list should have exactly four elements where each element is either a 'yes' or 'no'.\n"
    # main_query += "In the 'reasoning' key provide a list of strings which explains how you came to your conclusion for each of the four questions. In each explanation ensure to point to specific elements of the image so that you're not just making up reasons.\n"

    main_query += "Return the answers as only a JSON with a two keys 'reasoning' and 'ranswerseasoning'.\n"
    main_query += "In the 'reasoning' key provide a list of strings which explains how you came to your conclusion for each of the four questions. In each explanation ensure to point to specific elements of the image so that you're not just making up reasons.\n"
    main_query += "In the 'answers' key provide the answer as list consisting of 'yes' and 'no' by thinking things through in a step-by-step fashion. Ensure that no premable or explanation is included. Recall you need to answer questions (1) to (4) so this list should have exactly four elements where each element is either a 'yes' or 'no'.\n"


    llm_results = image_query(main_query, [input_image])
    parsed_results = parse_llm_json(llm_results)

    print()
    print(parsed_results)
    print()

    query_answers = parsed_results['answers']
    query_reasoning = parsed_results['reasoning']
    query_answers_TorF = [(a == 'yes') or (a == 'yes,') for a in query_answers]

    return query_answers_TorF, query_reasoning


class Agent_ReflectionOnImageList(BaseNode):
    """
    The Agent_ReflectionOnImageList node analyzes a batch of generated images against a set of quality criteria,
    including object visibility, composition, background, and adherence to custom directions. Images that don't
    meet the criteria are regenerated with improved prompts.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "text_prompt": ("STRING", {
                    "default" : "",
                    "multiline": True,
                    "placeholder": "Original text prompt that generated the images.",
                    "tooltip": "Original text prompt that generated the images.",
                    "agent_description": "The original prompt used to generate the images that will be analyzed."
                }),
                "custom_user_directions": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Custom user directions for how to evaluate whether or not an image should be retained as is or should be re-generated.",
                    "tooltip": "Custom user directions for how to evaluate whether or not an image should be retained as is or should be re-generated.",
                    "agent_description": "Specific criteria and guidelines for evaluating image quality and determining if regeneration is needed."
                }),
                "images": ("IMAGE", {
                    "default": [],
                    "tooltip": "List of images to analyze and reflect upon.",
                    "agent_description": "Images to be evaluated against quality criteria and potentially regenerated."
                }),
                "object_list": ("LIST", {
                    "default" : [],
                    "tooltip": "List object descriptions.",
                    "agent_description": "List of descriptions for the objects that should appear in the images."
                }),
            },
            "optional":
            {
                "output_folder": ("STRING", {
                    "default" : get_output_directory(),
                    "tooltip": "Location to save images to.",
                    "agent_description": "Directory path where regenerated images will be saved."
                }),
                "num_processes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": cpu_count(),
                    "tooltip": "Number of parallel processes.",
                    "agent_description": "Number of parallel processes for analyzing multiple images simultaneously. Deafult 1"
                }),
                "seed": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "tooltip": "Random seed for reproducible results. Manually set to 'fixed' to ensure the seed does not change.",
                    "agent_description": "Seed value for reproducible image generation when regenerating images. Default 1."
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING" )
    RETURN_NAMES = ("UpdatedImagesBasedOnReflection_images", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The final set of images after analysis and possible regeneration.",
        "Detailed explanation of the reflection process, including which images passed or failed criteria and why."
    )

    def execute(self, text_prompt, custom_user_directions, images, object_list, output_folder, num_processes, seed):

        tensor_list = convert_batch_tensor_to_tensor_list(images)
        image_list = [convert_from_torch_to_PIL(t) for t in tensor_list]

        n_objects = len(object_list)
        n_images = len(image_list)

        print(f"n_objects={n_objects}, n_images={n_images}")
        print(object_list)
        print(image_list)

        pbar = comfy.utils.ProgressBar(n_objects)

        def checklist_all_good(L):
            res = True
            for item in L: res = res and item
            return res

        global num_images_reflected_on
        num_images_reflected_on = 0

        def reflect_on_image(img, 
                             prompt: str, 
                             obj_descr: str, 
                             custom_instruct: str, 
                             seed_val: int,
                             img_idx: int, 
                             n_imgs: int,
                             progress_bar: comfy.utils.ProgressBar):
            """
            Reflect on an image and regenerate if it doesn't pass all the checklist requirements.
            """
            global num_images_reflected_on, unit_prompt_transform

            str_reflection_display = ""

            print(f"Reflecting on image [{img_idx}/{n_imgs}] ... ")

            checklist_results, checklist_reasoning = run_through_check_list_compressed(img, obj_descr, custom_instruct)
            
            print(f"Checklist results: {checklist_results}")

            if checklist_all_good(checklist_results):
                str_reflection_display += f"Image #{img_idx+1} has PASSED all checklist items.\n\n"
                num_images_reflected_on += 1
                progress_bar.update_absolute(num_images_reflected_on, n_objects, ("PNG", img, None))
                return convert_from_PIL_to_torch(img), str_reflection_display

            else:
                str_reflection_display += f"Image #{img_idx+1} was generated with the prompt: '{obj_descr}'\n"
                if checklist_results[0] == False: str_reflection_display += f"* FAILED object_is_centered_and_fully_visible. Reasoning: {checklist_reasoning[0]}.\n"
                if checklist_results[1] == False: str_reflection_display += f"* FAILED image_has_only_one_object. Reasoning: {checklist_reasoning[1]}.\n"
                if checklist_results[2] == False: str_reflection_display += f"* FAILED has_blank_white_background. Reasoning: {checklist_reasoning[2]}.\n"
                if checklist_results[3] == False: str_reflection_display += f"* FAILED adheres_to_user_directions. Reasoning: {checklist_reasoning[3]}.\n"

                new_prompt, new_prompt_reasoning = run_prompt_transform(obj_descr, checklist_results, prompt, custom_instruct)

                str_reflection_display += f"\nRegenerating Image #{img_idx} with new prompt:\n\n\n{new_prompt}\n\n"
                str_reflection_display += f"Reasoning for new prompt: {new_prompt_reasoning}\n\n"
                str_reflection_display += "----\n\n"

                desired_n_images = 1 # TODO: determine how to handle multiple images per object
                request_results, request_id = component_text_to_image(
                    prompt= f"wbgmsst. {new_prompt}. Candid, full body view, side camera angle.  White matte background with bright, indirect lighting",
                    num_images= desired_n_images,
                    seed=seed_val,
                    lora_scale=0.8,
                    lora_weights= "https://huggingface.co/gokaygokay/Flux-Game-Assets-LoRA-v2"
                )

                PIL_img = download_image_from_url_to_PIL(request_results[0])
                img_torch = convert_from_PIL_to_torch(PIL_img)
                if output_folder: 
                    str_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    PIL_img.save(f"{output_folder}/reflected_image_{img_idx}_{str_timestamp}.png")

                num_images_reflected_on += 1
                progress_bar.update_absolute(num_images_reflected_on, n_objects, ("PNG", PIL_img, None))
                return img_torch, str_reflection_display




        # NOTE: the backend needs to 'threading' in order to avoid Pickle errors as joblib attempts to pickle all inputs and data to run things in parallel and causes issue with the comfy progress bar object
        all_results = Parallel(backend="threading", n_jobs=num_processes)(delayed(reflect_on_image)
                                                                            (
                                                                                image_list[i],
                                                                                text_prompt,
                                                                                object_list[i],
                                                                                custom_user_directions,
                                                                                seed,
                                                                                i,
                                                                                n_images,
                                                                                pbar
                                                                            ) for i in range(n_images))
        
        # accumulate all results
        updated_images = [] # each element should be a torch.Tensor
        str_display = ""
        
        for results in all_results:
            img_output, str_reflection = results
            updated_images.append(img_output)
            str_display += str_reflection

        batch_updated_images = torch.stack(updated_images, dim=0)
        return (batch_updated_images, str_display)

