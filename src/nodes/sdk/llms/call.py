from .constants import *

from ..sdk_client import get_client 
from ..get_status import get_status 

def llm_call(sys_prompt: str,
             human_prompt: str,
             params: dict = None,
             extra_params: dict = None,
             max_retry_attempts: int = 3):
    
    mpx_client = get_client()

    if params == None: params = {}
    if "temperature" not in params: params["temperature"] = DEFAULT_TEMPERATURE
    if "max_tokens" not in params: params["max_tokens"] = DEFAULT_MAX_TOKENS

    if extra_params == None: extra_params = {}
    if "model" not in params: params["model "] = DEFAULT_MODEL

    call_success = False
    attempt = 1
    while (call_success == False) and (attempt <= max_retry_attempts):
        try:
            llm_request = mpx_client.llms.call(
                user_prompt=human_prompt,
                system_prompt=sys_prompt,
                data_parms=params,
                extra_body=extra_params
            )
            llm_response = get_status(llm_request.request_id)

            if llm_response.status == "failed":
                print("llm_call() returned with failed status - retrying...")
            elif llm_response.status == "complete":
                call_success = True

                print("llm_call() - complete!")
                print("Results:")
                print(llm_response.outputs.output)
                print()
                return llm_response.outputs.output
            
        except Exception as e:
            print(f"llm_call() -- Error:\n{e}\nwhen trying to obtain a response - retrying...")
            continue

        finally:
            attempt += 1
            if attempt > max_retry_attempts:
                raise Exception(f"llm_call() -- Failed to get a valid response after {max_retry_attempts} attempts!")

