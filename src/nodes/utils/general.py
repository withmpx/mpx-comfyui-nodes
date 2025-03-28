import hashlib
import json
import hjson


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
    
