import os
import logging
from aiohttp import web
from server import PromptServer
from mpx_genai_sdk import Masterpiecex

logger = logging.getLogger(__name__)

# Check if the route is already registered
if not hasattr(PromptServer.instance, '_mpx_comfyui_key_route_registered'):
    routes = PromptServer.instance.routes

    @routes.post('/mpx_comfyui_api_key')
    async def set_api_key(request: web.Request) -> web.Response:
        try:
            # Support both JSON and form-encoded payloads
            if request.content_type == 'application/json':
                data = await request.json()
            else:
                data = await request.post()
        except Exception as e:
            logger.error("Error parsing request payload: %s", e)
            return web.json_response({ "status": "error", "message": "Failed to parse request payload" }, status=400)

        api_key = data.get("api_key")
        if not api_key.strip():
            logger.warning("API key not provided in request")
            return web.json_response({ "status": "error", "message": "API key not provided" }, status=400)

        # Call your function to process/store the API key.
        result = setup_api_key(api_key)
        return web.json_response(result)

    # Mark the route as registered to avoid duplicate registration
    PromptServer.instance._mpx_comfyui_key_route_registered = True
else:
    logger.info("Route '/mpx_comfyui_api_key' already registered; skipping duplicate initialization.")

# Define the function to process/store the API key
def setup_api_key(api_key: str):
    if not api_key:
        return { "status": "error", "message": "API key is missing" }
    
    # Test the API key by creating a client and testing the connection
    try:
        _mpx_client = Masterpiecex(bearer_token = api_key)
        connection_test_result = _mpx_client.connection_test.retrieve()
        print(f"MPX: Connection test result: {connection_test_result}")
    except Exception as e:
        print(f"MPX: Error testing connection: {e}")
        return { "status": "error", "message": "API Key is invalid! Please check the key and try again." }
    
    # Determine the path for the .env file
    repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../user/default/mpx-comfyui-nodes"))
    env_path = os.path.join(repo_dir, ".env")
    # i.e. D:\comfu-ui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\user\default\mpx-comfyui-nodes\.env
    print(f"MPX: env file path: {env_path}")
    
    try:
        # Write or overwrite the .env file with the API key
        with open(env_path, "w") as env_file:
            env_file.write(f"MPX_SDK_BEARER_TOKEN={api_key}\n")
        
        # Optionally set secure file permissions (Unix-like systems)
        try:
            os.chmod(env_path, 0o600)
        except Exception as e:
            print(f"Warning: Unable to set file permissions on {env_path}: {e}")
        
        print("API key stored successfully!")
        return { "status": "success", "message": "API key stored successfully" }
    except Exception as e:
        print(f"Save API Key Error: {e}")
        return { "status": "error", "message": "Failed to store API key" }
    