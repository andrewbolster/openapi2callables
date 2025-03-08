# OpenAPI2Callables

[![pypi](https://img.shields.io/pypi/v/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![python](https://img.shields.io/pypi/pyversions/openapi2callables.svg)](https://pypi.org/project/openapi2callables/)
[![Docs](https://readthedocs.org/projects/openapi2callables/badge/?version=latest)](https://openapi2callables.readthedocs.io/en/latest/)
[![PyTest](https://github.com/andrewbolster/openapi2callables/actions/workflows/pytest.yml/badge.svg)](https://github.com/andrewbolster/openapi2callables/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/andrewbolster/openapi2callables/branch/main/graphs/badge.svg)](https://codecov.io/github/andrewbolster/openapi2callables)
[![BDOpenHub](https://www.openhub.net/p/openapi2callables/widgets/project_thin_badge.gif)](https://www.openhub.net/p/openapi2callables)

OpenAPI2Callables is a Python library for parsing and projecting OpenAPI endpoints into OpenAI/GenericLLM compatible Tools. It's designed to be flexible enough for non-LLM directed usage as well.

## Features

- Parse OpenAPI JSON/YAML schemas and extract basic parameter and response configurations
- Host a sample server for testing and demonstration
- Project tool definitions into OpenAI compatible tool definitions
- Provide runtime callbacks for tool execution

## Installation

You can install OpenAPI2Callables using pip:

```
pip install openapi2callables
```

## Quick Start

Here's a simple example of how to use OpenAPI2Callables:

```python
from openapi2callables import parse_spec, get_spec

# Load an OpenAPI specification
spec_url = "https://example.com/api/openapi.json"
spec = get_spec(spec_url)

# Parse the specification
tools = parse_spec(spec)

# Use the parsed tools in your application
for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Parameters: {tool.parameters}")
    print("---")
```

## CLI Usage

OpenAPI2Callables also provides a command-line interface:

```
openapi2callables parse https://example.com/api/openapi.json
openapi2callables serve
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Provide request authorization passthrough
- [ ] Enhance error handling and validation
- [ ] Add support for more complex OpenAPI features
- [ ] Improve documentation and examples
