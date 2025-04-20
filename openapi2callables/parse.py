"""Initial Parse module for OpenAPI spec files."""

import json
import logging

import jsonref
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
    spec = jsonref.replace_refs(spec)
    tools = {}
    paths = spec["paths"]
    for path, path_data in paths.items():
        if tool_prefix is not None and not path.startswith(tool_prefix):
            continue
        try:
            for method, method_data in path_data.items():
                logging.debug(f"Path: {path}")
                logging.debug(f"Method: {method}")
                logging.debug(f"Summary: {method_data['summary']}")
                logging.debug(f"Description: {method_data['description']}")
                logging.debug(f"Parameters: {method_data.get('parameters', [])}")
                logging.debug(f"RequestBody: {method_data.get('requestBody', [])}")
                logging.debug(f"Responses: {method_data['responses']}")

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
                            "_type": param.get("in", "path"),
                            "required": param["required"],
                            "type": normalised_type,
                            "description": param.get("description", ""),
                        }

                if "requestBody" in method_data:  # Handle request body parameters
                    for content_type, content_data in method_data["requestBody"]["content"].items():
                        for param_name, param_data in content_data["schema"]["properties"].items():
                            try:
                                param_spec = {
                                    "_type": "body",
                                    "required": param_name in content_data["schema"]["required"],
                                    "type": (
                                        param_data["type"]
                                        if "type" in param_data
                                        else [p["type"] for p in param_data["anyOf"] if p["type"] != "null"]
                                    ),
                                    "description": param_data.get("description", ""),
                                }
                                if param_name in parameters:
                                    # Param Name Collision; a parameter exists in the query parameters and the request body
                                    # This is a common pattern in OpenAPI specs, where a parameter can be passed in the query or the body
                                    # We will assume that both are needed, but to avoid naming conflicts, we will append "_body" to the body parameter
                                    parameters[param_name + "_body"] = param_spec
                                else:
                                    parameters[param_name] = param_spec
                            except KeyError as e:
                                raise KeyError(f"Error parsing {param_name}: {param_data}: {e}") from e

            tools[method_data["operationId"]] = {
                "path": path,
                "method": method,
                "summary": method_data["summary"],
                "description": method_data["description"],
                "parameters": parameters,
                "responses": method_data["responses"],
                "tags": method_data.get("tags", []),
            }
        except KeyError as e:
            logging.error(f"Error parsing {path}: {e}", exec_info=True)
        except Exception as e:
            logging.error(f"Error parsing {path}: {e}", exec_info=True)
            raise e

    return tools
