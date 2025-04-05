from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode


class TextToText(BaseNode):
    """
    The TextToText node transforms input text based on custom prompt instructions.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "input_text": ("STRING", {
                    "default" : "", 
                    "multiline": True,
                    "placeholder": "Input text to be updated based on user instructions.",
                    "tooltip": "Input text to be updated based on user instructions.",
                    "agent_description": "Input text to be updated based on user instructions."
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
                    "agent_description": "Temperature controls randomness. Lower values are more deterministic. Range: 0.0-1.0, default: 0.0."
                }),
                "custom_instructions": ("STRING", {
                    "default" : "",
                    "multiline": True,
                    "placeholder": "Custom instructions for how the text should be transformed. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Summarize this text'.",
                    "tooltip": "Custom instructions for how the text should be transformed. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Summarize this text'.",
                    "agent_description": "Custom instructions for how the text should be transformed. Examples: 'Make this more formal', 'Rewrite in a friendly tone', 'Summarize this text'. Default: empty string with multiline support."
                })
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("UpdatedText_string", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The transformed text based on the input and prompt instructions.",
        "Explanation of how the text was transformed based on the prompt instructions."
    )

    __DEFAULT_PROMPT_SYS = "You are an expert natural language editor who is tasked with understanding a given block of text and transforming it based on some custom user given instructions. Read the given block of text and reason about what needs to be changed based on the custom user given instructions. The changes don't need to be massive (but can be) so be precise and really only make the changes as dictated to you by the given instructions.\n\nReturn the answer as only a JSON with a two keys 'updated_text' and 'reasoning'.\nIn the 'updated_text' key provide the text which is updated by the custom user instructions with no premable or explanation. Remember to consult the custom user instructions when making any updates.\nIn the 'reasoning' key provide an explaination for why you made the changes you did and how it correlates to the given custom user instructions."
    __DEFAULT_PROMPT_HUMAN = "### Here is the given block of text:\n{user_input}\n\n### Here are the custom user instructions:\n{custom_instructions}"

    def execute(self, input_text, model, temp, custom_instructions):
        llm_params = {}
        llm_params["temperature"] = temp

        extra_params = {}
        extra_params["model"] = model

        prompt_data = {}
        prompt_data['user_input'] = input_text
        prompt_data['custom_instructions'] = custom_instructions

        sys_prompt = variable_substitution(TextToText.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TextToText.__DEFAULT_PROMPT_HUMAN, prompt_data)

        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

        updated_text = parsed_response['updated_text']
        llm_reasoning = parsed_response['reasoning']

        return updated_text, llm_reasoning



