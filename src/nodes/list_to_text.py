from .sdk.llms.call import llm_call
from .utils.general import hash_node_inputs, parse_llm_json, variable_substitution

from ..base import BaseNode


class StringListToText(BaseNode):
    """
    The StringListToText node combines a list of strings into a single text output based on custom instructions.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "string_list": ("LIST", 
                {
                    "default": [], 
                    "tooltip": "List of strings to combine into one string.",
                    "agent_description": "List of strings to be combined into a single text."
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
                    "agent_description": "Controls randomness in text merging. Range: 0.0-1.0, default: 0.0."
                }),
                "custom_instructions": ("STRING", {
                    "default" : "",
                    "multiline": True,
                    "placeholder": "Custom instructions for how the text should be transformed. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Summarize this text'.",
                    "tooltip": "Custom instructions for how the text should be transformed. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Summarize this text'.",
                    "agent_description": "Instructions for how to combine and transform the list of strings."
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", )
    RETURN_NAMES = ("MergedText_string", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The combined text output from merging the list of strings.",
        "Explanation of how the strings were combined based on the instructions."
    )

    __DEFAULT_PROMPT_SYS = "You are an expert natural language editor who is tasked with understanding a given list of strings and combining them all into a single block of text based on some custom user given instruction. Read each of the strings in the given list and reason about how to merge them into a single block of text based on the custom user instructions. The final merged result doesn't need to be overly long (but can be) so be precise and really only produce the result as dictated to you by the given instructions.\n\nReturn the answer as only a JSON with a two keys 'merged_text' and 'reasoning'.\nIn the 'merged_text' key provide the merged text which is the result of combining the list of strings based on the custom user instructions with no premable or explanation. Remember to consult the custom user instructions when making the merge.\nIn the 'reasoning' key provide an explaination for how you came to your result and why you merged it the way you did. Ensure that your reasoning includes correlations to the given custom user instructions."
    __DEFAULT_PROMPT_HUMAN = "### Here is the given block of text:\n{string_list}\n\n### Here are the custom user instructions:\n{custom_instructions}"


    def execute(self, string_list, model, temp, custom_instructions):
        llm_params = {}
        llm_params["temperature"] = temp

        extra_params = {}
        extra_params["model"] = model

        prompt_data = {}
        prompt_data['string_list'] = string_list
        prompt_data['custom_instructions'] = custom_instructions

        sys_prompt = variable_substitution(StringListToText.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(StringListToText.__DEFAULT_PROMPT_HUMAN, prompt_data)

        llm_response = llm_call(sys_prompt, human_prompt, llm_params, extra_params)
        parsed_response = parse_llm_json(llm_response)

        merged_text = parsed_response['merged_text']
        reasoning = parsed_response['reasoning']

        return (merged_text, reasoning, )
