# system imports
from joblib import Parallel, delayed, cpu_count

# comfy imports
import comfy.utils


# MPX imports
from .sdk.llms.call import llm_call
from .utils.general import hash_node_inputs, parse_llm_json, variable_substitution

from ..base import BaseNode


class StringListToStringList(BaseNode):
    """
    The StringListToStringList node transforms each string in a list based on custom instructions, processing them independently.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "string_list": ("LIST", 
                {
                    "default": [], 
                    "tooltip": "List of strings to modify into another list of strings based on user instructions. Each string is modified independently.",
                    "agent_description": "List of strings to be transformed independently."
                })
            },
            "optional":
            {
                "model": (["gpt-4o", "gpt-4o-mini"], "COMBO"),
                "temp": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,                    
                    "display": "slider",
                    "tooltip": "Temperature controls randomness. Lower values are more deterministic.",
                    "agent_description": "Controls randomness in text transformation. Range: 0.0-1.0, default: 0.0."
                }),
                "num_processes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": cpu_count(),
                    "tooltip": "Number of parallel processes for modifying the strings in the input list. Higher values speed up processing but use more system resources.",
                    "agent_description": "Number of parallel processes for batch processing. Default: 1."
                }),
                "custom_instructions": ("STRING", {
                    "default" : "",
                    "multiline": True,
                    "placeholder": "Custom instructions for how each string in the list should be modified. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Turn this into a prompt for image generation'.",
                    "tooltip": "Custom instructions for how each string in the list should be modified. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Turn this into a prompt for image generation'.",
                    "agent_description": "Instructions for how to transform each string in the list."
                }),
            }
        }
    
    RETURN_TYPES = ("LIST", "STRING", )
    RETURN_NAMES = ("UpdatedListOfStrings_list", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The list of transformed strings.",
        "Detailed explanation of how each string was transformed."
    )

    __DEFAULT_PROMPT_SYS = "You are an expert natural language editor who is tasked with understanding a given block of text and transforming it based on some custom user given instructions. Read the given block of text and reason about what needs to be changed based on the custom user given instructions. The changes don't need to be massive (but can be) so be precise and really only make the changes as dictated to you by the given instructions.\n\nReturn the answer as only a JSON with a two keys 'updated_text' and 'reasoning'.\nIn the 'updated_text' key provide the text which is updated by the custom user instructions with no premable or explanation. Remember to consult the custom user instructions when making any updates.\nIn the 'reasoning' key provide an explaination for why you made the changes you did and how it correlates to the given custom user instructions."
    __DEFAULT_PROMPT_HUMAN = "### Here is the given block of text:\n{user_input}\n\n### Here are the custom user instructions:\n{custom_instructions}"

    def execute(self, string_list, model, temp, num_processes, custom_instructions):
        llm_model = model
        llm_temp = temp

        global num_strings_modified
        num_strings_modified = 0

        n_strings = len(string_list)
        pbar = comfy.utils.ProgressBar(n_strings)

        def modify_string_list(s: str, 
                               custom_instruct: str, 
                               str_idx: int, 
                               n_strs: int,
                               progress_bar: comfy.utils.ProgressBar):
            global num_strings_modified
            
            print(f"Modifying string [{str_idx}/{n_strs}] ... ")

            llm_params = {}
            llm_params["temperature"] = temp

            extra_params = {}
            extra_params["model"] = model

            prompt_data = {}
            prompt_data['user_input'] = s
            prompt_data['custom_instructions'] = custom_instruct

            sys_prompt = variable_substitution(StringListToStringList.__DEFAULT_PROMPT_SYS, prompt_data)
            human_prompt = variable_substitution(StringListToStringList.__DEFAULT_PROMPT_HUMAN, prompt_data)


            llm_response = llm_call(sys_prompt, human_prompt, llm_params, extra_params)
            parsed_response = parse_llm_json(llm_response)

            updated_text = parsed_response['updated_text']
            reasoning = parsed_response['reasoning']

            str_modification_reasoning = f"Original: {s}\n"
            str_modification_reasoning += f"Updated: {updated_text}\n"
            str_modification_reasoning += f"Reasoning: {reasoning}\n\n"

            num_strings_modified += 1
            progress_bar.update_absolute(num_strings_modified, n_strings, None)
            return updated_text, str_modification_reasoning

        # NOTE: the backend needs to 'threading' in order to avoid Pickle errors as joblib attempts to pickle all inputs and data to run things in parallel and causes issue with the comfy progress bar object
        all_results = Parallel(backend="threading", n_jobs=num_processes)(delayed(modify_string_list)(
            string_list[i], 
            custom_instructions,
            i, 
            n_strings,
            pbar
        ) for i in range(n_strings))

        # accumulate all results
        updated_string_list = [] # each element should be a string
        all_reasoning = ""

        for results in all_results:
            updated_string, str_reasoning = results
            updated_string_list.append(updated_string)
            all_reasoning += str_reasoning


        return (updated_string_list, all_reasoning, )
