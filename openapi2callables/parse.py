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
        response = client(self.method, f"{self.base_url}{self.path}", params=kwds)
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
                            "type": p["schema"]["type"],
                            "description": p["schema"]["title"],
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
