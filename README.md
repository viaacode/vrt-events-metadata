# VRT Events Metadata

## Synopsis

This service will handle all events that should result in an update of the metadata. 
The incoming metadata gets transformed using the [mtd-transformer](https://github.com/viaacode/mtd-transformer/).

## Prerequisites

- Git
- Docker (optional)
- Python 3.10+
- Access to the [meemoo PyPi](http://do-prd-mvn-01.do.viaa.be:8081)

## Diagrams

<details>
  <summary>Sequence diagram (click to expand)</summary>

  ![VRT Events Metadata](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/viaacode/vrt-events-metadata/master/docs/v-e-m_sequence-diagram.plantuml&fmt=svg)

</details>

## Usage

1. Clone this repository with:

   `$ git clone https://github.com/viaacode/vrt-events-metadata.git`

2. Change into the new directory.

3. Set the needed config:

    Included in this repository is a `config.yml.example` file. 
    All values in the config have to be set in order for the application to function correctly.
    You can use `!ENV ${EXAMPLE}` as a config value to make the application get the `EXAMPLE` environment variable.

### Running locally

**Note**: As per the aforementioned requirements, this is a Python3
application. Check your Python version with `python --version`. You may want to
substitute the `python` command below with `python3` if your default Python version
is < 3. In that case, you probably also want to use `pip3` command.

1. Start by creating a virtual environment:

    `$ python -m venv env`

2. Activate the virtual environment:

    `$ source env/bin/activate`

3. Install the external modules:

    ```
    $ pip install -r requirements.txt \
        --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
        --trusted-host do-prd-mvn-01.do.viaa.be && \
      pip install -r requirements-test.txt
    ```

4. Run the tests with:

    `$ pytest -v --cov=./app`

5. Run the application:

    `$ python main.py`


### Running using Docker

1. Build the container:

   `$ docker build -t vrt-events-metadata .`

2. Run the container (with specified `.env` file):

   `$ docker run --env-file .env --rm vrt-events-metadata:latest`
