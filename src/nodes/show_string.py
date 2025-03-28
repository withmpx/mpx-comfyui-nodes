from PIL import Image
import torch
import numpy as np

from ..base import BaseNode

class ShowString(BaseNode):
    """
    The ShowString node displays a string input but does not return any values. Used for visualization purposes.
    """
    
    def __init__(self):
        self.version = "1.0"

    @classmethod
    def INPUT_TYPES(s): # will be defined in the js file
        return {
            "required": {
                "string_in": ("STRING", {
                    "default": "", 
                    "defaultInput": True,
                    "tooltip": "Input string to display",
                    "agent_description": "The string to be displayed."
                }),
            },
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    RETURN_AGENT_DESCRIPTIONS = ()
    OUTPUT_NODE = True

    def execute(self, string_in):
        return {"ui": {"list": (str(string_in),)}, "result": (str(string_in),)}
    
    @classmethod
    def IS_CHANGED(s, string_in):
        return float("NaN")
