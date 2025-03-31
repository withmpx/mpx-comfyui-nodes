# Data display
from .src.nodes.show_list import ShowList
from .src.nodes.show_string import ShowString

# Data I/O
from .src.nodes.load_image_data import LoadImageData
from .src.nodes.save_models_to_disk import SaveModelsToDisk

# Data selection
from .src.nodes.pick_from_list_of_strings import PickFromListOfStrings

# Data transformation - basic
from .src.nodes.text_to_text import TextToText
from .src.nodes.text_x2_to_text import TwoTextToText
from .src.nodes.text_to_list import TextToList
from .src.nodes.list_to_list import StringListToStringList
from .src.nodes.list_to_text import StringListToText

# Data transformations - creative
from .src.nodes.text_to_object_list import TextToObjectList
from .src.nodes.text_to_story import TextToStory
from .src.nodes.text_to_script_breakdown import TextToScriptBreakdown
from .src.nodes.object_list_to_image_list import ObjectListToImageList

# Agents
from .src.nodes.agent_pick_best_image_from_list import Agent_PickBestImageFromList
from .src.nodes.agent_reflect_on_image_list import Agent_ReflectionOnImageList

# MPX GenAI SDK functions
from .src.nodes.images_to_3dmodels import ImagesTo3DModels

# MPX GenAI SDK components
from .src.nodes.text_to_image import TextToImage

from .src.setup_api_key_server import setup_api_key


NODE_CLASS_MAPPINGS = {
    # Data display
    "ShowList" : ShowList,
    "ShowString" : ShowString,

    # Data I/O
    "LoadImageData": LoadImageData,
    "SaveModelsToDisk": SaveModelsToDisk,

    # Data selection
    "PickFromList": PickFromListOfStrings,

    # Data transforms - basic
    "TextToText": TextToText,
    "TwoTextToText": TwoTextToText,
    "TextToList": TextToList,
    "StringListToText": StringListToText,
    "StringListToStringList": StringListToStringList,

    # Data transformations - creative
    "TextToObjectList": TextToObjectList,
    "TextToStory": TextToStory,
    "TextToScriptBreakdown": TextToScriptBreakdown,
    "ObjectListToImageList": ObjectListToImageList,

    # Agents
    "Agent_PickBestImageFromList": Agent_PickBestImageFromList,
    "Agent_ReflectionOnImageList": Agent_ReflectionOnImageList,

    # MPX GenAI SDK functions
    "ImagesTo3DModels": ImagesTo3DModels,

    # MPX GenAI SDK components
    "TextToImage": TextToImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Data display
    "ShowList": "Show List",
    "ShowString": "Show String",

    # Data I/O
    "LoadImageData": "Load Image Data",
    "SaveModelsToDisk": "Download 3D models from URL(s)",

    # Data selection
    "PickFromList": "Select from StringList",

    # Data transforms - basic
    "TextToText": "Text To Text",
    "TwoTextToText": "Merge Text Blocks",
    "TextToList": "Text to StringList",
    "StringListToText": "StringList to Text",
    "StringListToStringList": "StringList to StringList",

    # Data transforms - creative
    "TextToObjectList": "Text to ObjectList",
    "TextToStory": "Text to Story",
    "TextToScriptBreakdown": "Script Breakdown",
    "ObjectListToImageList": "ObjectList to ImageList",

    # Agents
    "Agent_PickBestImageFromList": "Agent: Image Select",
    "Agent_ReflectionOnImageList": "ReflectionAgent: ImageList",

    # MPX GenAI SDK functions
    "ImagesTo3DModels": "Image(s) to 3D Model(s)",

    # MPX GenAI SDK components
    "TextToImage": "Text to Image(s)",
}

WEB_DIRECTORY = "./src/js"
__all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY", "NODE_DISPLAY_NAME_MAPPINGS"]

IP_VERSION = "1.0"