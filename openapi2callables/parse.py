"""Initial Parse module for OpenAPI spec files."""
import json

import requests
import yaml


def get_spec(spec_url):
    """Get the OpenAPI spec from a URL."""
    if spec_url.endswith(".yaml"):
        response = requests.get(spec_url)
        spec = yaml.safe_load(response.text)
    elif spec_url.endswith(".json"):
        response = requests.get(spec_url)
        spec = json.loads(response.text)
    else:
        raise ValueError("Unsupported file type, must be .yaml or .json")

    return spec


def parse_spec(spec, tool_prefix=None):
    """Parse the OpenAPI spec."""
    tools = {}
    paths = spec["paths"]
    for path, path_data in paths.items():
        if tool_prefix is not None and not path.startswith(tool_prefix):
            continue
        for method, method_data in path_data.items():
            print(f"Path: {path}")
            print(f"Method: {method}")
            print(f"Summary: {method_data['summary']}")
            print(f"Description: {method_data['description']}")
            print(f"Parameters: {method_data.get('parameters', [])}")
            print(f"Responses: {method_data['responses']}")
            print("\n")

            parameters = {}
            if "parameters" in method_data:  # Handle simple query parameters
                for param in method_data["parameters"]:
                    parameters[param["name"]] = {
                        "_type": "query" if param.get("in", "") == "query" else "path",
                        "required": param["required"],
                        "type": param["schema"]["type"],
                        "description": param.get("description", ""),
                    }
        tools[method_data["operationId"]] = {
            "path": path,
            "method": method,
            "summary": method_data["summary"],
            "description": method_data["description"],
            "parameters": parameters,
            "responses": method_data["responses"],
        }

    return tools
