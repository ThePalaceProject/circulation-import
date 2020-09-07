#FROM nypl/circ-exec:development
FROM viacheslavbessonov/circ-exec:lcp

# Need to be passed for using private PyPI repo
ARG PYPI_URL
ARG PYPI_USER
ARG PYPI_PASSWORD
ARG DEV=0

RUN apt update && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt install software-properties-common make gcc curl python3.7 python3-pip -y && \
    python3.7 -m pip install pip

WORKDIR /circulation-import
COPY poetry.lock pyproject.toml Makefile README.md /circulation-import/

# Bug in poetry config
RUN mkdir -p ~/.config/pypoetry/ && \
# We want to copy our code at the last layer but not to break poetry's "packages" section
    mkdir -p /circulation-import/src/circulation_import && \
    touch /circulation-import/src/circulation_import/__init__.py

RUN make install BIN=/usr/local/bin/ DEV=$DEV

COPY . /circulation-import

ENTRYPOINT ["python3.7", "-m", "circulation_import"]
