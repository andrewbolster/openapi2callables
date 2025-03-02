"""Initial Parse module for OpenAPI spec files."""

import json
import jsonref
import requests
import yaml
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class APITool:
    operationId: str
    description: str
    parameters: Dict[str, Any] = field(hash=False, compare=False)
    base_url: str
    path: str
    method: str = "get"
    summary: str = field(default=None, repr=False)
    responses: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __hash__(self):
        return hash(self.operationId)

    def __post_init__(self):
        if self.summary is not None:
            # prepend the description with the summary
            self.description = f"{self.summary}\n\n{self.description}"

    def __call__(self, client=requests.request, *args, **kwds):
        print(f"Calling {self.operationId} with {kwds}")
        body = {}
        for k, v in kwds.items():
            if self.parameters[k]['_type'] == 'body':
                body[k] = v
        response = client(self.method, f"{self.base_url}{self.path}", params=kwds, json=body)
        if hasattr(response, "json"):  # requests
            return response.json()
        else:  # httpx or otherwise
            return response.content

    def to_tool_spec(self):
        return {
            "type": "function",
            "function": {
                "name": self.operationId,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {
                            "type": p["type"],
                            "description": p["description"],
                        }
                        for k, p in self.parameters.items()
                    },
                    "required": [
                        k for k, p in self.parameters.items() if p["required"]
                    ],
                },
            },
        }


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
    spec = jsonref.replace_refs(spec)
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
            print(f"RequestBody: {method_data.get('requestBody', [])}")
            print(f"Responses: {method_data['responses']}")
            print("\n")

            parameters = {}
            if "parameters" in method_data:  # Handle simple query parameters
                for param in method_data["parameters"]:
                    normalised_type = None
                    if 'type' in param["schema"]:
                        normalised_type = param["schema"]["type"]
                    elif 'anyOf' in param["schema"]:
                        # Handle query parameters with multiple types
                        normalised_type = param["schema"]["anyOf"][0]["type"]
                        normalised_type = [p['type'] for p in param["schema"]["anyOf"] if p['type'] != 'null']
                    parameters[param["name"]] = {
                        "_type": "query" if param.get("in", "") == "query" else "path",
                        "required": param["required"],
                        "type":  normalised_type,
                        "description": param.get("description", ""),
                    }

            if "requestBody" in method_data:  # Handle request body parameters
                for content_type, content_data in method_data["requestBody"]["content"].items():
                    for param_name, param_data in content_data["schema"]["properties"].items():
                        try:
                            parameters[param_name] = {
                                "_type": "body",
                                "required": param_name in content_data["schema"]["required"],
                                "type": param_data["type"] if "type" in param_data else [p['type'] for p in param_data["anyOf"] if p['type'] != 'null'],
                                "description": param_data.get("description", ""),
                            }
                        except KeyError:
                            print(f"Error parsing {param_name}: {param_data}")
                            raise
            
        tools[method_data["operationId"]] = {
            "path": path,
            "method": method,
            "summary": method_data["summary"],
            "description": method_data["description"],
            "parameters": parameters,
            "responses": method_data["responses"],
        }

    return tools
