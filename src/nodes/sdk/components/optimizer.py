from ..sdk_client import get_client 
from ..get_status import get_status 
from io import BytesIO
import requests

# This function takes either a request_id, an image url or an image object and returns a 3d model
def component_optimizer(
                            mesh_url=None,
                            mesh_request_id=None,
                            target_ratio=0.85,
                            output_format="glb",
                            object_type="object"
                           ):
  client = get_client()
     
  # if mesh_url is provided, we upload the glb file and get the request_id
  if mesh_url:
    mesh_request_id = upload_glb(mesh_url)
  
  if mesh_request_id is None:
    raise ValueError("mesh_request_id or mesh_url is required")
  
  optimze_glb = client.components.optimize(
    asset_request_id= mesh_request_id,
    target_ratio= target_ratio,
    output_file_format= output_format,
    object_type= object_type
  )
  print(optimze_glb)
      # wait for the request to complete
  optimze_glb_response = get_status(optimze_glb.request_id)
  print(f'status_response: {optimze_glb_response}')

  if optimze_glb_response.status != 'complete':
    raise ValueError(f'optimze_glb request failed with status: {optimze_glb_response.status}')
  
  # Retrieve the optimized 3D object urls
  # example response
  # StatusRetrieveResponse(outputs=None, output_url='https://storage.googleapis.com/processors-bucket.masterpiecex.com/api-sessions/google-oauth2|106513587070086030188/unknown_appid/ml-requests_CUDNC0oowbeoV9MTnhFz/exports/optimized.fbx', processing_time_s=4.815, progress=None, request_id='CUDNC0oowbeoV9MTnhFz', status='complete', requestId='CUDNC0oowbeoV9MTnhFz', processingTime_s=4.815, outputUrl='https://storage.googleapis.com/processors-bucket.masterpiecex.com/api-sessions/google-oauth2|106513587070086030188/unknown_appid/ml-requests_CUDNC0oowbeoV9MTnhFz/exports/optimized.fbx')

  print("Optimized 3D object urls:")
  print(f'{output_format}: {optimze_glb_response.output_url}')

  # return the glb url
  return {
    "model_url": optimze_glb_response.output_url,
    "request_id": optimze_glb_response.request_id
  }

def upload_glb(glb_url: str):
  mpx_client = get_client()
  print(f">> uploading glb file to mpx: {glb_url}")
  print(f">> getting asset ID for the glb file")
  # create asset ID for the glb file
  asset_resp = mpx_client.assets.create(
      description="User uploaded glb.",
      name=f"model.glb",
      type="model/glb",
  )
  print(f">> asset_resp: {asset_resp}")
  print(f">> downloading the glb file")
  # download the glb file
  glb_resp = requests.get(glb_url)
  glb_byte_arr = BytesIO(glb_resp.content)
  glb_byte_arr.seek(0)
  glb_byte_arr = glb_byte_arr.getvalue()
  headers = {
      'Content-Type': 'model/glb',  # Usually not needed with `files`
  }
  print(f"Uploading glb file to: {asset_resp.asset_url}")
  # actually upload the glb file
  # TODO: do error handling here for upload_response.status_code
  upload_response = requests.put(asset_resp.asset_url, data=glb_byte_arr, headers=headers)
  print(f">> upload_response: {upload_response}")

  return asset_resp.request_id   