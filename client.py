import os
from citrine import Citrine

if __name__ == "__main__":
	client = Citrine(host=os.environ["CITRINE_DEV_HOST"], api_key=os.environ["CITRINE_DEV_API_KEY"])
