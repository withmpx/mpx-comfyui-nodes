import hashlib
import json
import hjson

from ..sdk.llms.call import llm_call
from ..sdk.llms.image_query import image_query, image_query_from_urls


def hash_node_inputs(inputs: dict) -> str:
    """ 
    Serialize the inputs deterministically 
    """
    inputs_serialized = json.dumps(inputs, sort_keys=True)
    return hashlib.md5(inputs_serialized.encode('utf-8')).hexdigest()


def parse_llm_json(s: str):
    """
    Assume s is a JSON or JSON-like string.
    Return a dict that the JSON represents.
    """
    text = s.strip()

    # strip away the extra markdown data if it exists
    if text[0:8] == "```json\n" and text[-4:] == "\n```":
        text = text[8:]
        text = text[:-4]

    json_data = hjson.loads(text)

    # additional parsing of strings
    parsed_json_data = {}
    for k, v in json_data.items():
        if isinstance(v, str):
            # adjust the raw string so that it's formatted properly
            adjusted = v.replace("\\n", "\n")
            adjusted = adjusted.replace("\\", "\"")
            parsed_json_data[k] = adjusted
        elif isinstance(v, list):
            new_list = []
            for ele in v:
                # hacky work around for strings because if it's in a list it's very possible to include the trailing "," character
                if isinstance(ele, str):
                    if ele[-1] == ',':
                        new_list.append(ele[:-1])
                    else:
                        new_list.append(ele)
                else:
                    new_list.append(ele)
            parsed_json_data[k] = new_list
        else:
            parsed_json_data[k] = v

    return parsed_json_data
    

def variable_substitution(prompt: str, data: dict):
    return prompt.format(**data)
    

def llm_call_with_json_parsing(sys_prompt: str, 
                               human_prompt: str, 
                               llm_params: dict, 
                               extra_params: dict,
                               max_retry_attempts: int = 3):
    call_success = False
    attempt = 1
    while (call_success == False) and (attempt <= max_retry_attempts):
        try:
            llm_response = llm_call(sys_prompt, human_prompt, llm_params, extra_params)
            parsed_response = parse_llm_json(llm_response)
            call_success = True
            return parsed_response
        
        except Exception as e:
            print(f"llm_call_with_json_parsing() -- Error:\n{e}\nwhen trying to obtain a valid JSON response - retrying...")
            continue

        finally:
            attempt += 1
            if attempt > max_retry_attempts:
                raise Exception(f"llm_call_with_json_parsing() -- Failed to get a valid response after {max_retry_attempts} attempts!")

def image_query_with_with_json_parsing(query: str,
                                       input_images: list,
                                       max_retry_attempts: int = 3,
                                       **kwargs):
    call_success = False
    attempt = 1
    input_image_urls = None
    while (call_success == False) and (attempt <= max_retry_attempts):
        try:
            # first attempt? need to get the image urls that were uploaded for possible retry attempts
            if input_image_urls is None:
                llm_results, input_image_urls = image_query(query, input_images, return_image_urls=True)

            # re-use the uploaded image URLs in the retry attempts
            else:
                llm_results = image_query_from_urls(query, input_image_urls)

            parsed_response = parse_llm_json(llm_results)
            call_success = True
            return parsed_response

        except Exception as e:
            print(f"image_query_with_with_json_parsing() -- Error:\n{e}\nwhen trying to obtain a valid JSON response - retrying...")
            continue

        finally:
            attempt += 1
            if attempt > max_retry_attempts:
                raise Exception(f"image_query_with_with_json_parsing() -- Failed to get a valid response after {max_retry_attempts} attempts!")
