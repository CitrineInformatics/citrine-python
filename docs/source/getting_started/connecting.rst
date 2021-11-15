======================================
Connecting to the Citrine Platform
======================================

The Citrine Python client connects to the Citrine Platform API.
To create a client, you must specify the specific site that you want to connect to and your API key, so
assuming that your Citrine deployment is ``https://matsci.citrine-platform.com``:

.. code-block:: python

    from citrine import Citrine
    import os
    citrine_client = Citrine(host="matsci.citrine-platform.com", api_key=os.environ.get("CITRINE_API_KEY"))

Your API key serves both as your identity and your password.
Anyone with your API key can take actions as you would on the platform.
Therefore, you should keep your API key out of scripts and sources files.
A better option is to define your API key as an environment variable, as in the example above.
If you've accidentally exposed your API key, you can revoke it and create a new one via the browser interface.
