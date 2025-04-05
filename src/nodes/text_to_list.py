from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode


class TextToList(BaseNode):
    """
    The TextToList node breaks down input text into a structured list of strings based on custom instructions.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "input_text": ("STRING", {
                    "default": "", 
                    "multiline": True,
                    "placeholder": "The text to be broken down into a list of strings. Can be any block of text that needs to be structured into separate items.",
                    "tooltip": "The text to be broken down into a list of strings. Can be any block of text that needs to be structured into separate items.",
                    "agent_description": "Text input that will be broken down into a list of strings."
                }),
            },
            "optional":
            {
                "temp": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,                    
                    "display": "slider",
                    "tooltip": "Controls how the text is split into items. Lower values create more predictable splits, higher values allow more creative.",
                    "agent_description": "Controls randomness in text splitting. Range: 0.0-1.0, default: 0.0."
                }),
                "custom_instructions": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "User instructions for how to break down the text into a list of strings.",
                    "tooltip": "User instructions for how to break down the text into a list of strings.",
                    "agent_description": "Instructions specifying how to break down the text into a list."
                }),
            }
        }
    
    RETURN_TYPES = ("LIST", "STRING")
    RETURN_NAMES = ("ResultingList_list", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The list of strings extracted from the input text.",
        "Explanation of how the text was broken down into a list."
    )

    __DEFAULT_PROMPT_SYS = "You are an expert natural language editor who is tasked with breaking down a block of text into a list of strings based on some custom user given instructions. Read the given block of text and reason about what's important and needs to be extracted into a seperate string based on the custom user given instructions. If no custom instructions are given then just split it however you want in a way that makes sense.\n\nReturn the answer as only a JSON with a two keys 'list_of_strings' and 'reasoning'.\nIn the 'list_of_strings' key provide the list of strings that were extracted from the block of text according to the custom user instructions with no premable or explanation.\nIn the 'reasoning' key provide an explaination for why the merged version makes sense how it correlates to the given custom user instructions."
    __DEFAULT_PROMPT_HUMAN = "### Here is the block of text:\n{user_input}\n\n### Here are the custom user instructions:\n{custom_instructions}"

    def execute(self, input_text, temp, custom_instructions):
        llm_params = {}
        llm_params["temperature"] = temp

        extra_params = {}
        extra_params["model"] = "gpt-4o"

        prompt_data = {}
        prompt_data['user_input'] = input_text
        prompt_data['custom_instructions'] = custom_instructions

        sys_prompt = variable_substitution(TextToList.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TextToList.__DEFAULT_PROMPT_HUMAN, prompt_data)

        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)
        
        updated_text = parsed_response['list_of_strings']
        llm_reasoning = parsed_response['reasoning']

        return updated_text, llm_reasoning
