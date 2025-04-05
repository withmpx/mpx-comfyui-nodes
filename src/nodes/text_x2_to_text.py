from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing
from ..base import BaseNode


class TwoTextToText(BaseNode):
    """
    The TwoTextToText node combines two text inputs into a single text output based on custom instructions.
    """

    @classmethod 
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "input_text_a": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "First text input to be combined.",
                    "tooltip": "First text input to be combined.",
                    "agent_description": "First text input to be merged with the second text."
                }),
                "input_text_b": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Second text input to be combined.",
                    "tooltip": "Second text input to be combined.",
                    "agent_description": "Second text input to be merged with the first text."
                }),
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
                    "default": "",
                    "multiline": True,
                    "placeholder": "Custom instructions for how to process the two texts together.",
                    "tooltip": "Custom instructions for how to process the two texts together.",
                    "agent_description": "Instructions specifying how to merge the two text inputs."
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("MergedText_string", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The combined text output from merging the two input texts.",
        "Explanation of how the texts were merged based on the instructions."
    )

    __DEFAULT_PROMPT_SYS = "You are an expert natural language editor who is tasked with understanding two blocks of text and the merging them into one block of text based on some custom user given instructions. Read the each given block of text and reason about what needs to be done in order to merge them based on the custom user given instructions. The merged version doesn't need to be massive (but can be) so be precise and really only make the changes as dictated to you by the given instructions. If no custom instructions are given then just concatenate the two blocks of text in a seamless manner.\n\nReturn the answer as only a JSON with a two keys 'updated_text' and 'reasoning'.\nIn the 'updated_text' key provide the text which is the merged version that respects the custom user instructions with no premable or explanation. Remember to consult the custom user instructions when making any updates.\nIn the 'reasoning' key provide an explaination for why the merged version makes sense how it correlates to the given custom user instructions."
    __DEFAULT_PROMPT_HUMAN = "### Here is the first block of text:\n{user_input_a}\n\n### Here is the second block of text:\n{user_input_b}\n\n### Here are the custom user instructions:\n{custom_instructions}"

    def execute(self, input_text_a, input_text_b, model, temp, custom_instructions):
        llm_params = {}
        llm_params["temperature"] = temp

        extra_params = {}
        extra_params["model"] = model

        prompt_data = {}
        prompt_data['user_input_a'] = input_text_a
        prompt_data['user_input_b'] = input_text_b
        prompt_data['custom_instructions'] = custom_instructions

        sys_prompt = variable_substitution(TwoTextToText.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TwoTextToText.__DEFAULT_PROMPT_HUMAN, prompt_data)

        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

        updated_text = parsed_response['updated_text']
        llm_reasoning = parsed_response['reasoning']

        return updated_text, llm_reasoning
