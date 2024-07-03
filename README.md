# OpenAPI2Tools

[![pypi](https://img.shields.io/pypi/v/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![python](https://img.shields.io/pypi/pyversions/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![Build Status](https://github.com/andrewbolster/openapi2callables/actions/workflows/dev.yml/badge.svg)](https://github.com/andrewbolster/openapi2callables/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/andrewbolster/openapi2callables/branch/main/graphs/badge.svg)](https://codecov.io/github/andrewbolster/openapi2callables)

Experiment in parsing and projecting OpenAPI endpoints into OpenAI/GenericLLM compatible Tools (but should also be generic enough for non-llm directed usage...)

-   Documentation: <https://andrewbolster.github.io/openapi2callables>
-   GitHub: <https://github.com/andrewbolster/openapi2callables>
-   PyPI: <https://pypi.org/project/openapi2callables/>
-   Free software: Apache-2.0

## Features

-   [x] Gather `openapi.json/yaml` schemas, and extract basic parameter and response configurations. (`openapi2tool parse`)
-   [x] Host a 'sample' server (`openapi2tool serve`)
-   [ ] Project tool definitions into OpenAI compatible tool definitions
-   [ ] Provide runtime-callbacks for tool execution
-   [ ] Provide request authorization passthrough
