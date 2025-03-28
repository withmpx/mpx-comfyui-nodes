# system imports
from joblib import Parallel, delayed, cpu_count

# comfyui imports 
import comfy.utils   # type: ignore[reportMissingImports]   Note: this is ignored because it's not an error when Comfy imports it.

# sdk imports
from .sdk.functions.image_to_3d import function_image_to_3d
from .sdk.utils.image_helpers import download_image_from_url_to_PIL, convert_from_PIL_to_torch, convert_batch_tensor_to_tensor_list
from .utils.general import hash_node_inputs
from ..base import BaseNode


class ImagesTo3DModels(BaseNode):
    """
    The ImageTensorsTo3DModels node processes an image to generate a 3D model. Returns a thumbnail image and 3D model URLs for each processed image.
    """
    def __init__(self):
        self._cached_input_hash = None
        self._cached_output = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {
                    "tooltip": "The input image or batch of images to be converted into a 3D model.",
                    "agent_description": "A required images to be converted into 3D models."
                }),
            },
            "optional": {
                "texture_size": ([512, 1024, 2048], {
                    "default": 1024,
                    "tooltip": "Resolution of generated textures (512, 1024, or 2048)",
                    "agent_description": "Defines the resolution for textures in the generated 3D models."
                }),
                "seed": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000000,
                    "tooltip": "Random seed for reproducible results",
                    "agent_description": "A fixed seed used if 'use_random_seeds' is disabled, ensuring repeatable generation results."
                }),
                "num_processes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": cpu_count(),
                    "tooltip": "Number of parallel processes for batch processing.",
                    "agent_description": "Number of parallel processes."
                })
            },
        }

    RETURN_TYPES = ("IMAGE", "LIST", "LIST", "LIST", "LIST")
    RETURN_NAMES = ("ThumbnailsOfModels_images", "GLBUrls_list", "FBXUrls_list", "USDZUrls_list", "RequestIDs_list")
    RETURN_AGENT_DESCRIPTIONS = (
        "A set of thumbnail images generated from the processed input images.",
        "A list of URLs to the generated GLB 3D models.",
        "A list of URLs to the generated FBX 3D models.",
        "A list of URLs to the generated USDZ 3D models.",
        "A list of request IDs corresponding to each 3D model generation call."
    )

    def execute(self, images, texture_size, seed, num_processes):
        """
            image: batch of torch.Tensors or single torch.Tensor (pixel values ranges from 0.0 to 1.0)

        """
        global num_3dmodels_processed
        num_3dmodels_processed = 0
        def genarate_3dmodel_from_image(img, img_idx: int, n_imgs: int, progress_bar: comfy.utils.ProgressBar):
            """
            Generate a 3D model from a single image tensor.
            """
            global num_3dmodels_processed

            print(f"Processing 3D Model [{img_idx}/{n_imgs}] ... ")

            imageto3d_response = function_image_to_3d(
                image=img,
                texture_size=texture_size, 
                seed=seed) 
            
            print(f"imageto3d_response [{img_idx}/{n_imgs}]: {imageto3d_response}")
            
            # for some reason the progress-bar preview for images has to be a PNG
            # TODO: determine if a tensor truely cannot be displayed as part of the progress
            img_progress = download_image_from_url_to_PIL(imageto3d_response['thumbnail_url'])
            img_thumbnail = convert_from_PIL_to_torch(img_progress)
            
            # update the comfy progress bar if one is given
            if progress_bar is not None:
                num_3dmodels_processed += 1
                progress_bar.update_absolute(num_3dmodels_processed, n_imgs, ("PNG", img_progress, None))

            return img_thumbnail, imageto3d_response['glb_url'], imageto3d_response['fbx_url'], imageto3d_response['usdz_url'], imageto3d_response['request_id']



        if texture_size not in [512, 1024, 2048]:
            raise ValueError(f"texture_size must be one of: 512, 1024, 2048! Got: {texture_size}")

        # check if the inputs have changed
        input_hash = hash_node_inputs({
            "image_data": images.tolist(),
            "texture_size": texture_size,
            "seed": seed
        })

        # re-run the function if the hashes differ
        if input_hash != self._cached_input_hash:

            input_images = convert_batch_tensor_to_tensor_list(images)

            ret_dict = {}
            ret_dict["thumbnail_images"] = []
            ret_dict["glb_urls"] = []
            ret_dict["fbx_urls"] = []
            ret_dict["usdz_urls"] = []
            ret_dict["request_ids"] = []

            n_images = len(input_images)
            pbar = comfy.utils.ProgressBar(n_images)

            if num_processes == 1:
                for i in range(n_images):
                    img_thumbnail, glb_url, fbx_url, usdz_url, request_id = genarate_3dmodel_from_image(input_images[i],
                                                                                                        i,
                                                                                                        n_images,
                                                                                                        pbar)
                    ret_dict["thumbnail_images"].append(img_thumbnail)
                    ret_dict["glb_urls"].append(glb_url)
                    ret_dict["fbx_urls"].append(fbx_url)
                    ret_dict["usdz_urls"].append(usdz_url)
                    ret_dict["request_ids"].append(request_id)

            else:
                # NOTE: the backend needs to 'threading' in order to avoid Pickle errors as joblib attempts to pickle all inputs and data to run things in parallel and causes issue with the comfy progress bar object
                all_results = Parallel(backend="threading", n_jobs=num_processes)(delayed(genarate_3dmodel_from_image)(
                    input_images[i],
                    i,
                    n_images,
                    pbar
                ) for i in range(n_images))
                
                # accumulate the results into the returned dictionary
                for results in all_results:
                    ret_dict["thumbnail_images"].append(results[0])
                    ret_dict["glb_urls"].append(results[1])
                    ret_dict["fbx_urls"].append(results[2])
                    ret_dict["usdz_urls"].append(results[3])
                    ret_dict["request_ids"].append(results[4])


            self._cached_output = (ret_dict["thumbnail_images"], ret_dict["glb_urls"], ret_dict["fbx_urls"], ret_dict["usdz_urls"], ret_dict["request_ids"])
            self._cached_input_hash = input_hash

        return self._cached_output

