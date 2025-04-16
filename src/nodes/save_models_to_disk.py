# system imports
import os
import datetime

# comfyui imports
from folder_paths import get_output_directory
import comfy.utils

# MPX GenAI imports
from ..base import BaseNode
from .sdk.utils.model_helpers import download_model_to_disk_from_url
from .utils.general import hash_node_inputs


class SaveModelsToDisk(BaseNode):
    """
    The SaveModelsToDisk node saves model URLs to disk and returns the file paths of the saved models.
    """
    
    def __init__(self):
        self._cached_input_hash = None
        self._cached_output = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_urls": ("LIST", {
                    "default": [],
                    "forceInput": True,
                    "tooltip": "List of URLs of 3D models to be downloaded",
                    "agent_description": "A list of model URLs to be saved to disk."
                }),
            },
            "optional": {
                "output_folder": ("STRING", {
                    "default": get_output_directory(),
                    "tooltip": "Local directory where the downloaded models will be saved",
                    "agent_description": "The folder where the models will be saved. Default: system output directory."
                })
            },
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("FilePathsOfModels_list",)
    RETURN_AGENT_DESCRIPTIONS = (
        "A list of file paths where the models were saved on disk.",
    )
    OUTPUT_NODE = True

    def execute(self, model_urls, output_folder):

        results = []

        print("save_models_to_disk")
        print(model_urls)
        print(output_folder)

        if os.path.exists(output_folder) == False:
            print(f"Output folder: {output_folder} DOES NOT EXIST!")
            output_folder = get_output_directory()
            print(f"Defaulting to: {output_folder}")

        # Check if the inputs have changed
        input_hash = hash_node_inputs({
            "model_urls": model_urls,
            "output_folder": output_folder,
        })

        # Initialize the dictionary to be returned
        output_results = { "ui": { "3d_models": [] } }

        if input_hash != self._cached_input_hash:

            local_filepaths = []
            n_models = len(model_urls)
            pbar = comfy.utils.ProgressBar(n_models)
            for idx in range(n_models):
                str_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"model_{idx}_{str_timestamp}"
                model_path = download_model_to_disk_from_url(model_urls[idx],
                                                             output_folder,
                                                             filename)
                local_filepaths.append(model_path)
                pbar.update_absolute(idx+1, n_models)

                url_filename, url_file_ext = os.path.splitext(model_urls[idx])
                filename_with_extension = f"{filename}{url_file_ext}"


                # Append directly to the return structure
                output_results["ui"]["3d_models"].append({
                    "filename": filename_with_extension,
                    "subfolder": output_folder,
                    "type": "output",
                })

            self._cached_output = (local_filepaths,)
            self._cached_input_hash = input_hash

        print("-- Results --")
        print(output_results["ui"]["3d_models"]) # Print the list we built
        #return self._cached_output
        return output_results
