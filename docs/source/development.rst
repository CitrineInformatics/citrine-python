Development
===========

Development of Citrine-Python requires 100% unit test coverage, pep-8 compliance and working Sphinx documentation.

Running tests in Docker
-----------------------

Running these tests in Docker will ensure that you are using a consistent development environment to Travis CI, our
continuous integration server.  See the file .travis.yml in the repository root for more information.

Build the Container
*******************

Run this command from the repository root.  This will tag the image with as "citrine-python":

`docker build -f scripts/Dockerfile.pytest -t citrine-python .`

Run the Tests
*************

Run the Docker container with default parameters to run all unit tests:

`docker run --rm -it citrine-python`

Specify a path to run all the tests in one test module, in this case 'test_table.py'.  Note: running a subset of unit
tests will report a low unit test coverage metric:

`docker run --rm -it citrine-python tests/serialization/test_table.py`

Specify a specific test to run:

`docker run --rm -it citrine-python tests/serialization/test_table.py::test_simple_deserialization`

See the `PyTest documentation <https://docs.pytest.org/en/latest/usage.html>`_ for more information.

Running an Interactive Shell
****************************

Run this command to get an interactive bash shell in the Docker container, overriding the default entrypoint:

`docker run --rm -it --entrypoint bash citrine-python`
