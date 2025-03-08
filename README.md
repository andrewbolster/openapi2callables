# OpenAPI2Tools

[![pypi](https://img.shields.io/pypi/v/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![python](https://img.shields.io/pypi/pyversions/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![Docs](https://readthedocs.org/projects/openapi2callables/badge/?version=latest)](https://openapi2callables.readthedocs.io/en/latest/)
[![PyTest](https://github.com/andrewbolster/openapi2callables/actions/workflows/pytest.yml/badge.svg)](https://github.com/andrewbolster/openapi2callables/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/andrewbolster/openapi2callables/branch/main/graphs/badge.svg)](https://codecov.io/github/andrewbolster/openapi2callables)
[![BDOpenHub](https://www.openhub.net/p/openapi2callables/widgets/project_thin_badge.gif)](https://www.openhub.net/p/openapi2callables)

Experiment in parsing and projecting OpenAPI endpoints into OpenAI/GenericLLM compatible Tools (but should also be generic enough for non-llm directed usage...)

## Features / Todo List

-   [x] Gather `openapi.json/yaml` schemas, and extract basic parameter and response configurations. (`openapi2tool parse`)
-   [x] Host a 'sample' server (`openapi2tool serve`)
-   [x] Project tool definitions into OpenAI compatible tool definitions
-   [x] Provide runtime-callbacks for tool execution
-   [ ] Provide request authorization passthrough
