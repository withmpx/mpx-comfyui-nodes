from .utils.general import hash_node_inputs, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode


class TextToObjectList(BaseNode):
    """
    The TextToObjectList node generates a list of object descriptions from a text prompt.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "text_prompt": ("STRING", 
                {
                    "default": "", 
                    "multiline": True,
                    "placeholder": "Enter a description of a scene or environment. The node will extract relevant objects that should be present.",
                    "tooltip": "Enter a description of a scene or environment. The node will extract relevant objects that should be present.",
                    "agent_description": "The text prompt to generate object descriptions from."
                }),
                "min_objects": ("INT",
                {
                    "default": 1,
                    "min": 1,
                    "tooltip": "Minimum number of objects to extract from the description. Must be at least 1.",
                    "agent_description": "The minimum number of objects to generate. Default: 1."
                }),
                "max_objects": ("INT", 
                {
                    "default": 4,
                    "min": 1,
                    "tooltip": "Maximum number of objects to extract. The node will stop at this number even if more objects could be identified.",
                    "agent_description": "The maximum number of objects to generate. Default: 4."
                })
            }
        }

    RETURN_TYPES = ("LIST", )
    RETURN_NAMES = ("ObjectDescriptions_list",)
    RETURN_AGENT_DESCRIPTIONS = (
        "A list of generated object descriptions based on the input text prompt.",
    )

    __DEFAULT_PROMPT_SYS = "You are a natural language expert who is an expert at breaking down a block of text into a list of objects. This block of text does not necessarily contain the objects itself and can be generic descriptions so your job is to find a set of objects which find the description and the intention of the user. For example, if the block of text is 'I want a scene of a living room', then you should return objects which should exist in a common living room.\n\nReturn the answer as only a JSON with a two keys 'objects' and 'reasoning'. In the 'objects' key provide the list of objects with no premable or explanation. Each object in the list should be more descriptive than just the object itself. Ensure the list has a minimum of {min_objects} items and at most {max_objects} items. In the 'reasoning' key provide an explanation for why the objects was chosen. Just the JSON only is returned."
    __DEFAULT_PROMPT_HUMAN = "Here is the block of text: {user_input}"


    def execute(self, text_prompt, min_objects, max_objects):
        llm_params = {}
        llm_params["temperature"] = 0.0

        extra_params = {}
        extra_params["model"] = "gpt-4o"

        prompt_data = {}
        prompt_data['min_objects'] = min_objects
        prompt_data['max_objects'] = max_objects
        prompt_data['user_input'] = text_prompt

        sys_prompt = variable_substitution(TextToObjectList.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TextToObjectList.__DEFAULT_PROMPT_HUMAN, prompt_data)

        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

        print(parsed_response)

        object_descr_list = parsed_response['objects']
        n_objects = len(object_descr_list)

        # truncate the object list if it's bigger than max_objects
        # do nothing (for now) if the object list is less than min_objects
        if n_objects > max_objects:
            object_descr_list = object_descr_list[:max_objects]

        return (object_descr_list, )
