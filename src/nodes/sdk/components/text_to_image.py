from ..sdk_client import get_client 
from ..get_status import get_status 

def component_text_to_image(prompt, num_images, seed, lora_scale, lora_weights):
    client = get_client()
    images_from_text = client.components.text2image(
        prompt=prompt,
        num_images=num_images,
        num_steps= 4,
        seed=seed,
        lora_scale= lora_scale,
        lora_weights= lora_weights
    )
    print(images_from_text)
    images_from_text_resp = get_status(images_from_text.request_id)
    print(f"images_from_text_resp: {images_from_text_resp}")
    image_list = images_from_text_resp.outputs.images
    return (image_list, images_from_text.request_id)

