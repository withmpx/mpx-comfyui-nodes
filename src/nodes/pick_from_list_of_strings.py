from .utils.general import hash_node_inputs
from ..base import BaseNode


class PickFromListOfStrings(BaseNode):
    """
    The PickFromListOfStrings node selects a single item from a list of strings at the specified index.
    """
    
    def __init__(self):
        self._cached_input_hash = None
        self._cached_output = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_list": ("LIST", {
                    "default": [],
                    "tooltip": "List of items to select from",
                    "agent_description": "The input list of strings to select from."
                }),
            },
            "optional": {
                "index": ("INT", {
                    "default": 1,
                    "min": 1,
                    "tooltip": "Position of the item to select",
                    "agent_description": "Position of the item to select from the list."
                }),
            },
        }

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("SelectedItem_string",)
    RETURN_AGENT_DESCRIPTIONS = (
        "The selected string item from the input list.",
    )

    def execute(self, input_list, index):
        """
            input_list is a generic list of items
            index is the specifc element the user wants (-1 for the actual list index)
        """

        n_elements = len(input_list)

        if n_elements == 0: raise ValueError("Input list has no elements!")
        if index == 0: raise ValueError("Cannot pick a zero'th element from a list!")
        if index < 0: raise ValueError("The desired index number cannot be negative!")
        if index > n_elements: raise ValueError(f"Desired index number {index} is too large! The list only has {n_elements} elements.")

        # check if the inputs have changed
        input_hash = hash_node_inputs({
            "input_list": input_list,
            "index": index,
        })

        # re-run the function if the hashes differ
        if input_hash != self._cached_input_hash:
            actual_index = index - 1
            self._cached_output = (input_list[actual_index],)
            self._cached_input_hash = input_hash

        return self._cached_output

