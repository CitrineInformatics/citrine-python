======================================
Request Throttling
======================================


To prevent abuse of the citrine-python API, requests are limited to 300 per minute per IP address.
If this limit is exceeded, a 429 status code will be returned.