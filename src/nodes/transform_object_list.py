# system imports
from joblib import Parallel, delayed, cpu_count

# comfy imports
import comfy.utils

# MPX imports
from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode

class TransformObjectList(BaseNode):
    """
    The TransformObjectList node transforms a list of object descriptions based on scene context and custom instructions.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "object_list": ("LIST", {
                    "tooltip": "List of object descriptions to transform based on scene context and custom instructions.",
                    "agent_description": "List of object descriptions to be transformed."
                }),
                "scene_description": ("STRING", {
                    "default" : "",
                    "multiline" : True,
                    "placeholder": "Description of the scene or environment where these objects will be placed. Used to ensure object descriptions match the context.",
                    "tooltip": "Description of the scene or environment where these objects will be placed. Used to ensure object descriptions match the context.",
                    "agent_description": "Description of the story scene where the objects will be placed."
                }),
                "custom_instructions": ("STRING", {
                    "default" : "",
                    "multiline" : True,
                    "placeholder": "Specific instructions for how to modify the object descriptions. Examples: 'Make descriptions more detailed', 'Focus on material properties'.",
                    "tooltip": "Specific instructions for how to modify the object descriptions. Examples: 'Make descriptions more detailed', 'Focus on material properties'.",
                    "agent_description": "Instructions for how to modify the object descriptions."
                }),
                "temp": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider", 
                    "tooltip": "Controls creativity in transformations. Lower values (0.0-0.3) make changes more conservative, higher values (0.7-1.0) allow more creative modifications.",
                    "agent_description": "Controls creativity in transformations. Range: 0.0-1.0, default: 0.0."
                }),
                "num_processes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": cpu_count(),
                    "tooltip": "Number of parallel processes for transforming object descriptions. Higher values speed up processing but use more system resources.",
                    "agent_description": "Number of parallel processes for batch processing. Default: 1."
                })
            }
        }
    
    RETURN_TYPES = ("LIST", "STRING" )
    RETURN_NAMES = ("UpdatedObjectDescriptions_list", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The list of transformed object descriptions.",
        "Detailed explanation of how each object was transformed."
    )

    __DEFAULT_PROMPT_SYS = """You are a natural language expert who transforms object descriptions to match a specific style and context. Your task is to:

1. Review a user-provided description of an object
2. Evaluate if and how it fits within the context of the provided scene description
3. Consider the custom instructions for additional guidance on style and content
4. Return an updated description that better fits the context (or keep it unchanged if it already fits well)

Return ONLY a JSON with two keys:
- 'description': The updated object description with no preamble or explanation
- 'reasoning': Your explanation for why changes were made or why no changes were needed

Follow the custom instructions carefully as they contain important details about the transformation requirements.
"""

    __DEFAULT_PROMPT_HUMAN = "### Object description:\n\n{object_description}\n\n"
    __DEFAULT_PROMPT_HUMAN += "### Contextual info about the scene the object is in:\n\n{scene_description}\n\n"
    __DEFAULT_PROMPT_HUMAN += "### Custom instructions:\n\n{custom_instructions}\n\n"


    def execute(self, object_list, scene_description, custom_instructions, temp, num_processes):
        llm_params = {}
        llm_params["temperature"] = temp

        extra_params = {}
        extra_params["model"] = "gpt-4o"

        n_objects = len(object_list)
        pbar = comfy.utils.ProgressBar(n_objects)

        global num_transformed_obj_descr
        num_transformed_obj_descr = 0

        def transform_object_description(obj_desc: str,
                                         scene_desc: str,                                          
                                         custom_instruct: str, 
                                         obj_idx: int, 
                                         n_objs: int,
                                         progress_bar: comfy.utils.ProgressBar):
            
            global num_transformed_obj_descr

            prompt_data = {}
            prompt_data['object_description'] = obj_desc
            prompt_data['scene_description'] = scene_desc
            prompt_data['custom_instructions'] = custom_instruct

            sys_prompt = variable_substitution(TransformObjectList.__DEFAULT_PROMPT_SYS, prompt_data)
            human_prompt = variable_substitution(TransformObjectList.__DEFAULT_PROMPT_HUMAN, prompt_data)

            parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

            updated_object_description = parsed_response['description']
            LLM_reasoning = parsed_response['reasoning']
            print(f"Original Object: {obj_desc}")
            print(f"Updated Object: {updated_object_description}")
            print(f"Reasoning: {LLM_reasoning}")

            str_reasoning_display = ""
            str_reasoning_display += f"({obj_idx+1})\n"
            str_reasoning_display += f"\tOriginal: {obj_desc}\n"
            str_reasoning_display += f"\tUpdated: {updated_object_description}\n"
            str_reasoning_display += f"\tReasoning: {LLM_reasoning}\n"
            str_reasoning_display += "\n\n"

            num_transformed_obj_descr += 1
            progress_bar.update_absolute(num_transformed_obj_descr, n_objs, None)

            return updated_object_description, str_reasoning_display

        # NOTE: the backend needs to 'threading' in order to avoid Pickle errors as joblib attempts to pickle all inputs and data to run things in parallel and causes issue with the comfy progress bar object
        all_results = Parallel(backend="threading", n_jobs=num_processes)(delayed(transform_object_description)(
            object_list[i],
            scene_description,
            custom_instructions,
            i,
            n_objects,
            pbar
        ) for i in range(n_objects))

        # accumulate all results
        output_display_string = ""
        updated_object_list = []

        for results in all_results:
            transformed_obj_descr, transform_reasoning = results
            updated_object_list.append(transformed_obj_descr)
            output_display_string += transform_reasoning

        return (updated_object_list, output_display_string)
