"""Initial Parse module for OpenAPI spec files."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict

import jsonref
import requests
import yaml

from . import logger


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
        params = {}
        body = {}
        # To recover from the _body naming convention in parse_spec we need to identify
        # we add a 'virtual' kwds key for each body parameter
        kwds_list = list(kwds.items())
        # New virtual kwargs will be kwd_body for each kwd in kwds that appears in parameters
        shadowed_keys = {k: k[:-5] for k in self.parameters.keys() if k.endswith("_body")}
        if shadowed_keys:
            for key, kwd in shadowed_keys.items():
                kwds_list.append((key, kwds[kwd]))  # so this becomes {root_body: value_of_root}

        for k, v in kwds_list:
            if self.parameters[k]["_type"] == "body":
                if k.endswith("_body"):
                    k = k[:-5]
                body[k] = v
            if self.parameters[k]["_type"] == "path":
                self.path = self.path.replace(f"{{{k}}}", str(v))
            if self.parameters[k]["_type"] == "query":
                params[k] = v

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
                    "required": [k for k, p in self.parameters.items() if p["required"]],
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
            logger.debug(f"Path: {path}")
            logger.debug(f"Method: {method}")
            logger.debug(f"Summary: {method_data.get('summary', None)}")
            logger.debug(f"Description: {method_data.get('description'), None}")
            logger.debug(f"Parameters: {method_data.get('parameters', [])}")
            logger.debug(f"RequestBody: {method_data.get('requestBody', [])}")
            logger.debug(f"Responses: {method_data.get('responses', [])}")
            logger.debug("\n")

            parameters = {}
            if "parameters" in method_data:  # Handle simple query parameters
                for param in method_data["parameters"]:
                    normalised_type = None
                    if "type" in param["schema"]:
                        normalised_type = param["schema"]["type"]
                    elif "anyOf" in param["schema"]:
                        # Handle query parameters with multiple types
                        normalised_type = param["schema"]["anyOf"][0]["type"]
                        normalised_type = [p["type"] for p in param["schema"]["anyOf"] if p["type"] != "null"]
                    parameters[param["name"]] = {
                        "_type": "query" if param.get("in", "") == "query" else "path",
                        "required": param["required"],
                        "type": normalised_type,
                        "description": param.get("description", ""),
                    }

            if "requestBody" in method_data:  # Handle request body parameters
                for content_type, content_data in method_data["requestBody"]["content"].items():
                    for param_name, param_data in content_data["schema"].get("properties", {}).items():
                        try:
                            param_spec = {
                                "_type": "body",
                                "required": param_name in content_data["schema"].get("required", []),
                                "type": param_data["type"]
                                if "type" in param_data
                                else [p["type"] for p in param_data["anyOf"] if p["type"] != "null"],
                                "description": param_data.get("description", ""),
                            }
                            if param_name in parameters:
                                # Param Name Collision; a parameter exists in the query parameters and the request body
                                # This is a common pattern in OpenAPI specs, where a parameter can be passed in the query or the body
                                # We will assume that both are needed, but to avoid naming conflicts, we will append "_body" to the body parameter
                                parameters[param_name + "_body"] = param_spec
                            else:
                                parameters[param_name] = param_spec
                        except KeyError:
                            print(f"Error parsing {param_name}: {param_data}")
                            raise

        tools[method_data.get("operationId", "")] = {
            "path": path,
            "method": method,
            "summary": method_data.get("summary", ""),
            "description": method_data.get("description", ""),
            "parameters": parameters,
            "responses": method_data.get("responses", {}),
        }

    return tools
