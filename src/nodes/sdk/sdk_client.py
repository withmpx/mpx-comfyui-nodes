from dotenv import load_dotenv
import os
from mpx_genai_sdk import Masterpiecex  

def get_client():
    return _mpx_client

def _get_user_env_path():
    # get the path to the user's mpx-comfyui-nodes configuration directory
    # this is the directory where the user's .env file is stored
    # assume that this is a typical install location
    file_path = os.path.dirname(__file__)
    custom_nodes_path = os.path.abspath(os.path.join(file_path, "..", "..", "..", ".."))
    comfyui_path = os.path.abspath(os.path.join(custom_nodes_path, ".."))
    default_user_path = os.path.join(comfyui_path, "user", "default")
    mpx_comfyui_nodes_path = os.path.join(default_user_path, "mpx-comfyui-nodes")

    # check if the default user path exists
    if not os.path.exists(default_user_path):
        print(f"mpx-comfyui-nodes: Can't find default user directory: {default_user_path}")
        return None

    print(f"mpx-comfyui-nodes: user_path: {mpx_comfyui_nodes_path}")
    env_path = os.path.join(mpx_comfyui_nodes_path, ".env")

    # if this directory does not exist, try to create it and add an empty .env file
    if not os.path.exists(env_path):
        print(f"mpx-comfyui-nodes: Creating user directory: {mpx_comfyui_nodes_path}")
        try:
            os.makedirs(mpx_comfyui_nodes_path)
            with open(os.path.join(mpx_comfyui_nodes_path, ".env"), "w") as f:
                f.write("MPX_SDK_BEARER_TOKEN=<your_bearer_token_here>")
        except Exception as e:
            print(f"mpx-comfyui-nodes: Error creating user directory: {e}")
            raise e
    return os.path.join(mpx_comfyui_nodes_path, ".env")


load_dotenv(dotenv_path=_get_user_env_path())

bearer_token = os.getenv("MPX_SDK_BEARER_TOKEN")
if not bearer_token:
    # raise ValueError("MPX_SDK_BEARER_TOKEN is not set - please set it in the .env file ")
    # Print a warning instead of raising an exception to avoid breaking the entire node
    print("-" * 80)
    print("mpx-comfyui-nodes: MPX_SDK_BEARER_TOKEN is not set - please set it in the ComfyUI Settings")
    print("^" * 80)
elif bearer_token == "<your_bearer_token_here>":
    print("-" * 80)
    print("mpx-comfyui-nodes: MPX_SDK_BEARER_TOKEN is not set - please set it in the ComfyUI Settings")
    print("^" * 80)
else:
    print("mpx-comfyui-nodes: Got MPX SDK Bearer Token")
    try:
        _mpx_client = Masterpiecex(bearer_token = bearer_token)
        print(f"mpx-comfyui-nodes: MPX Connection test result: {_mpx_client.connection_test.retrieve()}")
    except Exception as e:
        print("-" * 150)
        print(f"mpx-comfyui-nodes: Error creating MPX client: {e.message}")
        print("^" * 150)

    