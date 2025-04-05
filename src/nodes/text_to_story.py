# from .sdk.llms.call import llm_call
from .utils.general import hash_node_inputs, parse_llm_json, variable_substitution, llm_call_with_json_parsing

from ..base import BaseNode


class TextToStory(BaseNode):
    """
    The TextToStory node generates a story based on a text prompt, genre, and other parameters.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":
            {
                "text_prompt": ("STRING", {
                    "default" : "", 
                    "multiline": True,
                    "placeholder": "Describe the main concept or theme of the story you want to generate.",
                    "tooltip": "Describe the main concept or theme of the story you want to generate.",
                    "agent_description": "Input text prompt to define what the overall story is about."
                }),
                "genre": (["Action", "Adventure", "Absurdist Fiction", "Comedy", "Children", "Crime", "Drama", "Historical Fiction", "Horror", "Mystery", "Romance", "Science Fiction", "Hard Science Fiction", "Thriller/Suspense", "Western", "Dystopian Fiction", "Cyberpunk", "Steampunk", "Magical Realism", "Paranormal Fiction", "Coming-of-Age (Bildungsroman)", "Satire", "Urban Fiction", "Mythic Fiction", "Political Fiction", "Speculative Fiction"], {
                    "tooltip": "Select the genre for your story. This will influence the writing style, themes, and narrative structure.",
                    "agent_description": "The genre of the story. Options include various fiction genres."
                }),
                "story_word_length": ("INT", {
                    "default": 150,
                    "min": 10,
                    "max": 2000,                    
                    "display": "slider",
                    "tooltip": "The approximate word count for the story.",
                    "agent_description": "The length of the story in words. Range: 10-2000, default: 150."
                }),
                "temperature": ("FLOAT", {
                    "default": 0.8,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider",
                    "tooltip": "Controls creativity in story generation. Higher values create more unexpected plot twists and creative elements and lower values are more structured and predicable.",
                    "agent_description": "Controls the randomness of the story generation. Range: 0.0-1.0, default: 0.8, step: 0.1."
                }),
                "custom_instructions": ("STRING", {
                    "default" : "",
                    "multiline": True,
                    "placeholder": "Additional specific instructions for story style, tone, or special requirements.",
                    "tooltip": "Additional specific instructions for story style, tone, or special requirements.",
                    "agent_description": "Any additional custom instructions for how the story should be told, formatted and/or styled."
                })
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("EntireStory_string", "AllCharacterProfiles_string", "Reasoning_string")
    RETURN_AGENT_DESCRIPTIONS = (
        "The generated story text.",
        "A list of characters featured in the generated story.",
        "Explanation of how the story was generated based on the input parameters."
    )

    __DEFAULT_PROMPT_SYS = "You are a master storyteller with expertise across multiple genres and narrative styles. Your task is to craft a compelling, original story based on the client's specifications. The client will provide: (1) The overall concept or theme of the story, (2) the desired genre, (3) preferred length, and optionally (4) custom instructions or stylistic preferences.\n\n"        
    __DEFAULT_PROMPT_SYS += "STORY STRUCTURE:\n"
    __DEFAULT_PROMPT_SYS += "- Begin with a strong hook that introduces the main character(s) and setting\n"
    __DEFAULT_PROMPT_SYS += "- Develop a clear narrative arc with rising action, climax, and resolution\n"
    __DEFAULT_PROMPT_SYS += "- Focus on a single compelling conflict unless otherwise requested below\n"
    
    __DEFAULT_PROMPT_SYS += "CHARACTER DEVELOPMENT:\n"
    __DEFAULT_PROMPT_SYS += "- Create memorable characters with distinct personalities, motivations, and flaws\n"
    __DEFAULT_PROMPT_SYS += "- Show character growth or change through the story's events\n"
    __DEFAULT_PROMPT_SYS += "- Ensure characters' decisions drive the plot forward\n\n"
    
    __DEFAULT_PROMPT_SYS += "GENRE CONSIDERATIONS:\n"
    __DEFAULT_PROMPT_SYS += "- Incorporate key elements and conventions of the specified genre\n"
    __DEFAULT_PROMPT_SYS += "- Balance genre tropes with original elements to avoid clichés\n\n"
    
    __DEFAULT_PROMPT_SYS += "WRITING STYLE:\n"
    __DEFAULT_PROMPT_SYS += "- Maintain a consistent tone appropriate to the genre and story concept\n"
    __DEFAULT_PROMPT_SYS += "- Use a mix of dialogue, description, and action to create a dynamic narrative\n"
    __DEFAULT_PROMPT_SYS += "- Show rather than tell when depicting emotions and character traits\n"
    __DEFAULT_PROMPT_SYS += "- Vary sentence structure and pacing to maintain reader interest\n\n"
    
    __DEFAULT_PROMPT_SYS += "Return the answer as only a JSON with three keys: 'story', 'characters', and 'reasoning'.\n"
    __DEFAULT_PROMPT_SYS += "- In 'story': Provide the complete narrative with appropriate paragraphing and dialogue formatting. No preamble or explanation.\n"
    __DEFAULT_PROMPT_SYS += "- In 'characters': Provide a numbered list of all characters in the story with detailed character profiles. Each character should be described in a concise description starting with a number followed by a period (e.g., '1. Character description...'). Include: their name, age and gender, personality traits and quirks, visual details, motivations and goals, relationships with other characters, and any significant character arcs or development throughout the story. Focus on elements that help understand their role in the narrative and their impact on the story's themes. Include the protagonist, antagonist, and any supporting characters. Do not use JSON formatting within this section.\n"
    __DEFAULT_PROMPT_SYS += "- In 'reasoning': Explain how the story fulfills the client's requirements, your narrative choices, and how the characters and their arcs serve the story's themes."
    __DEFAULT_PROMPT_SYS += "Make sure you return the answer as a JSON string with the ```json and ``` markers."

    __DEFAULT_PROMPT_HUMAN = "Here are the clients given information:\n\n"
    __DEFAULT_PROMPT_HUMAN += "### (1) The overall gist of what the story is about\n{story_gist}\n\n"
    __DEFAULT_PROMPT_HUMAN += "### (2) The genre of the story\n{story_genre}\n\n"
    __DEFAULT_PROMPT_HUMAN += "### (3) The target word count for the story\n{story_word_length}\n\n"
    __DEFAULT_PROMPT_HUMAN += "### (4) Set of custom instructions to incorporate\n{custom_instructions}\n\n"


    def execute(self, text_prompt, genre, story_word_length, temperature, custom_instructions):
        llm_params = {}
        llm_params["temperature"] = temperature

        extra_params = {}
        extra_params["model"] = "gpt-4o"

        prompt_data = {}
        prompt_data['story_gist'] = text_prompt
        prompt_data['story_genre'] = genre
        prompt_data['story_word_length'] = story_word_length
        prompt_data['custom_instructions'] = custom_instructions

        sys_prompt = variable_substitution(TextToStory.__DEFAULT_PROMPT_SYS, prompt_data)
        human_prompt = variable_substitution(TextToStory.__DEFAULT_PROMPT_HUMAN, prompt_data)

        # llm_response = llm_call(sys_prompt, human_prompt, llm_params, extra_params)
        # parsed_response = parse_llm_json(llm_response)
        
        parsed_response = llm_call_with_json_parsing(sys_prompt, human_prompt, llm_params, extra_params)

        generated_story = parsed_response['story']
        generated_characters = parsed_response['characters']
        llm_reasoning = parsed_response['reasoning']

        return generated_story, generated_characters, llm_reasoning



