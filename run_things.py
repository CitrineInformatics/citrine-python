import os

from citrine import Citrine


client = Citrine(
    api_key=os.environ.get("CITRINE_DEV_API_KEY"),
    scheme="https",
    host=os.environ.get("CITRINE_DEV_API_HOST"),
    port=None,
)


response = client.catalyst.insights("What is the melting point of Al?")

print(response.response)
