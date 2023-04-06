###########
Development
###########


*******
Sandbox
*******

Acquire sources, create Python virtualenv, install package and dependencies,
and run software tests::

    git clone https://github.com/daq-tools/lorrystream
    cd lorrystream
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --use-pep517 --prefer-binary --editable=.[test,develop,release]

    # Run linter and regular test suite.
    poe check


*****
Tests
*****

In order to speed up running the test suite multiple times, it is advised to
keep your auxiliary service instances running. For Mosquitto, this is handled
automatically by ``pytest-mqtt``. For CrateDB, you will need to define two
environment variables::

    export CRATEDB_KEEPALIVE=true


****************
Build OCI images
****************

OCI images will be automatically published to the GitHub Container Registry
(GHCR), see `LorryStream images on GHCR`_. If you want to build images on your
machine, you can use those commands::

    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    export BUILDKIT_PROGRESS=plain
    docker build --tag local/lorrystream --file release/oci/Dockerfile .

::

    docker run --rm -it local/lorrystream lorry --version
    docker run --rm -it local/lorrystream lorry info


.. _LorryStream images on GHCR: https://github.com/orgs/daq-tools/packages?repo_name=lorrystream
