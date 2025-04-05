from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode

class TextToScriptBreakdown(BaseNode):
    """
    The TextToScriptBreakdown node analyzes a film or animation script and extracts characters, props, and scene synopses.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "script_text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "The script or story text that needs to be broken down into production elements.",
                    "tooltip": "The script or story text that needs to be broken down into production elements.",
                    "agent_description": "The film/animation script text to analyze."
                })
            }
        }

    RETURN_TYPES = ("LIST", "LIST", "LIST", "STRING")
    RETURN_NAMES = ("CharactersInScript_list", "PropsInScript_list", "SynopsesPerSceneInScript_list", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "A list of characters identified in the script.",
        "A list of props identified in the script.",
        "A list of scene synopses extracted from the script.",
        "Explanation of how the script was analyzed and broken down."
    )

    __DEFAULT_PROMPT_SYS = (
        "You are an expert film and animation script analyst. You are provided with a complete script for a film or animation. "
        "Your task is to extract and return three items in JSON format: "
        "(1) a list of all characters mentioned in the script (including any relevant descriptions), "
        "(2) a list of all props and environment objects present in the script (including any interactive items), and "
        "(3) a list where each element is a brief synopsis of each distinct scene in the script. "
        "Return the result as a JSON object with the keys 'characters', 'props', 'scene_synopses' and 'reasoning'"
        "In the 'characters' key provide a list of all characters mentioned in the script (including any relevant descriptions). Each element in the list is just a string."
        "In the 'props' key provide a list of all props and environment objects present in the script (including any interactive items). Each element in the list is just a string."
        "In the 'scene_synopses' key provide a list where each element is a brief synopsis of each distinct scene in the script."
        "In the 'reasoning' key provide an explaination for how the three items (1) to (3) as mentioned above were extracted and why the extracted elements make sense."
    )

    __DEFAULT_PROMPT_HUMAN = (
        "### The following is the full film/animation script:\n\n{script_text}\n\n"
        "Extract the required elements as described."
    )

    def execute(self, script_text):
        llm_params = {}
        llm_params["temperature"] = 0.0

        extra_params = {}
        extra_params["model"] = "gpt-4o"

        prompt_data = {}
        prompt_data["script_text"] = script_text

        sys_prompt = variable_substitution(TextToScriptBreakdown.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TextToScriptBreakdown.__DEFAULT_PROMPT_HUMAN, prompt_data)

        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

        characters = parsed_response["characters"]
        props = parsed_response["props"]
        scene_synopses = parsed_response["scene_synopses"]
        llm_reasoning = parsed_response['reasoning']

        return characters, props, scene_synopses, llm_reasoning
