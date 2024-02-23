import openapi_client


configuration = openapi_client.Configuration(host="http://localhost")

with openapi_client.ApiClient(configuration) as api_client:
    api_instance = openapi_client.DefaultApi(api_client)

    some_settings = openapi_client.SomeSettings(mandatory1=1, mandatory2=2) # SomeSettings |  (optional)

    try:
        api_instance.something_post(some_settings=some_settings)
    except Exception as e:
        print(f"Error: {e}")



