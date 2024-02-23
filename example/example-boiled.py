import openapi_client
from boiled import boiled
Client = boiled(openapi_client)


with Client(host="http://localhost") as client:
    try:
        client.something_post(mandatory1=1, mandatory2=2)
    except Exception as e:
        print(f"Error: {e}")



