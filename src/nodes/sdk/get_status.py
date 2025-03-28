import time
from .sdk_client import get_client

def get_status(request_id):
    mpx_client = get_client()
    if not mpx_client:
        return None

    status_resp = mpx_client.status.retrieve(request_id)
    print(status_resp)
    # Wait until the object has been generated (status = 'complete')
    while status_resp.status not in ["complete", "failed"]:
        time.sleep(10)
        status_resp = mpx_client.status.retrieve(request_id)
        print ('*', end='')
    print('') # clears waiting indicators
    print(status_resp)
    return status_resp
