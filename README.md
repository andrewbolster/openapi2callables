# OpenAPI2Tools

[![pypi](https://img.shields.io/pypi/v/openapi2tools.svg)](https://pypi.org/project/openapi2tools/)
[![python](https://img.shields.io/pypi/pyversions/openapi2tools.svg)](https://pypi.org/project/openapi2tools/)
[![Build Status](https://github.com/andrewbolster/openapi2tools/actions/workflows/dev.yml/badge.svg)](https://github.com/andrewbolster/openapi2tools/actions/workflows/dev.yml)
[![codecov](https://codecov.io/gh/andrewbolster/openapi2tools/branch/main/graphs/badge.svg)](https://codecov.io/github/andrewbolster/openapi2tools)

Experiment in parsing and projecting OpenAPI endpoints into OpenAI/GenericLLM compatible Tools (but should also be generic enough for non-llm directed usage...)

-   Documentation: <https://andrewbolster.github.io/openapi2tools>
-   GitHub: <https://github.com/andrewbolster/openapi2tools>
-   PyPI: <https://pypi.org/project/openapi2tools/>
-   Free software: Apache-2.0

## Features

-   [x] Gather `openapi.json/yaml` schemas, and extract basic parameter and response configurations. (`openapi2tool parse`)
-   [x] Host a 'sample' server (`openapi2tool serve`)
-   [ ] Project tool definitions into OpenAI compatible tool definitions
-   [ ] Provide runtime-callbacks for tool execution
-   [ ] Provide request authorization passthrough
