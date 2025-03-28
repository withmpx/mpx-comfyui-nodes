from PIL import Image
import torch
import numpy as np

from ..base import BaseNode

class ShowList(BaseNode):
    """
    The ShowList node displays a list input but does not return any values. Used for visualization purposes.
    """
    
    def __init__(self):
        self.version = "1.0"

    @classmethod
    def INPUT_TYPES(s): # will be defined in the js file
        return {
            "required": {
                "list_in": ("LIST", {
                    "default": [],
                    "forceInput": True,
                    "tooltip": "Input list to display as text - can contain images, tensors, or other data types to be displayed in plain text format",
                    "agent_description": "The list to be displayed."
                }),
            },
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    RETURN_AGENT_DESCRIPTIONS = ()
    OUTPUT_NODE = True

    def execute(self, list_in = []):
        # change how the display is constructed per data type
        n_elements = len(list_in)
        list_display = ""
        for idx in range(n_elements):
            item_display = f"{idx+1}. "

            item = list_in[idx]

            if isinstance(item, Image.Image): 
                item_display += f"{item}: Image ({item.format}, {item.mode}, {item.size})"
            elif isinstance(item, (torch.Tensor, np.ndarray)): 
                item_display += f"{item.shape}, {item.dtype}"
            else: 
                item_display += f"{item}"
                
            list_display += (item_display + "\n")

        # If the UI widget exists, update its text content.
        return {"ui": {"list": (list_display,)}, "result": (list_in,)}
    
    @classmethod
    def IS_CHANGED(s, list_in):
        return float("NaN")
