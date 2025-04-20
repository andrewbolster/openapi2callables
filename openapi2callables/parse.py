"""Parse module for OpenAPI spec files with enhanced capabilities."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import jsonref
import requests
import yaml


def get_spec(spec_url_or_path: str) -> Dict[str, Any]:
    """
    Get the OpenAPI spec from a URL or local file path.

    Args:
        spec_url_or_path: URL or file path to the OpenAPI spec

    Returns:
        The parsed OpenAPI spec as a dictionary

    Raises:
        ValueError: If the file type is not supported or the file/URL cannot be accessed
    """

    # Check if the input is a URL
    try:
        result = urlparse(spec_url_or_path)
        is_url = all([result.scheme, result.netloc])
    except ValueError:
        is_url = False

    # Check if it's a local file
    if not is_url:
        if not os.path.exists(spec_url_or_path):
            raise ValueError(f"File not found: {spec_url_or_path}")
        try:
            if spec_url_or_path.endswith(".yaml") or spec_url_or_path.endswith(".yml"):
                with open(spec_url_or_path, "r") as f:
                    spec = yaml.safe_load(f)
            elif spec_url_or_path.endswith(".json"):
                with open(spec_url_or_path, "r") as f:
                    spec = json.load(f)
            else:
                raise ValueError("Unsupported file type, must be .yaml, .yml, or .json")
            return spec
        except Exception as e:
            logging.error(f"Error reading local file {spec_url_or_path}: {e}")
            raise ValueError(f"Could not read spec file: {e}")

    # If not a local file, try as URL
    try:
        if spec_url_or_path.endswith((".yaml", ".yml")):
            response = requests.get(spec_url_or_path)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            spec = yaml.safe_load(response.text)
        elif spec_url_or_path.endswith(".json"):
            response = requests.get(spec_url_or_path)
            response.raise_for_status()
            spec = json.loads(response.text)
        else:
            # Try to determine format from content-type header
            response = requests.get(spec_url_or_path)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                spec = json.loads(response.text)
            elif "application/yaml" in content_type or "application/x-yaml" in content_type:
                spec = yaml.safe_load(response.text)
            else:
                # Try JSON first, then YAML as fallback
                try:
                    spec = json.loads(response.text)
                except json.JSONDecodeError:
                    try:
                        spec = yaml.safe_load(response.text)
                    except yaml.YAMLError:
                        raise ValueError("Could not determine spec format from URL without extension")

        return spec
    except requests.RequestException as e:
        logging.error(f"Error fetching spec from URL {spec_url_or_path}: {e}")
        raise ValueError(f"Could not fetch spec from URL: {e}")


def parse_spec(
    spec: Dict[str, Any], tool_prefix: Optional[str] = None, include_deprecated: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Parse the OpenAPI spec into a dictionary of tools.

    Args:
        spec: The OpenAPI spec as a dictionary
        tool_prefix: Optional prefix to filter paths
        include_deprecated: Whether to include deprecated operations

    Returns:
        A dictionary of tools, keyed by operationId
    """
    spec = jsonref.replace_refs(spec)
    tools = {}
    paths = spec["paths"]

    # Extract components for reuse if available
    components = spec.get("components", {})
    schemas = components.get("schemas", {})  # noqa: F841

    for path, path_data in paths.items():
        if tool_prefix is not None and not path.startswith(tool_prefix):
            continue

        # Process each HTTP method for this path
        for method, method_data in path_data.items():
            if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                try:
                    # Skip deprecated operations if not explicitly included
                    if method_data.get("deprecated", False) and not include_deprecated:
                        logging.info(f"Skipping deprecated operation: {method.upper()} {path}")
                        continue

                    # Log operation details for debugging
                    logging.debug(f"Path: {path}")
                    logging.debug(f"Method: {method}")
                    logging.debug(f"Summary: {method_data.get('summary', 'No summary')}")
                    logging.debug(f"Description: {method_data.get('description', 'No description')}")
                    logging.debug(f"Parameters: {method_data.get('parameters', [])}")
                    logging.debug(f"RequestBody: {method_data.get('requestBody', {})}")
                    logging.debug(f"Responses: {method_data.get('responses', {})}")

                    # Initialize parameters dictionary
                    parameters = {}

                    # Process path, query, header, and cookie parameters
                    if "parameters" in method_data:
                        for param in method_data["parameters"]:
                            param_name = param["name"]
                            param_in = param.get("in", "query")
                            param_required = param.get("required", False)
                            param_schema = param.get("schema", {})
                            param_description = param.get("description", "")

                            # Extract parameter type
                            param_type = extract_type_from_schema(param_schema)

                            # Extract enum values if present
                            enum_values = param_schema.get("enum", None)

                            # Extract constraints
                            constraints = extract_constraints(param_schema)

                            # Create parameter spec
                            param_spec = {
                                "_type": param_in,
                                "required": param_required,
                                "type": param_type,
                                "description": param_description,
                            }

                            # Add enum values if present
                            if enum_values:
                                param_spec["enum"] = enum_values

                            # Add constraints if present
                            if constraints:
                                param_spec.update(constraints)

                            parameters[param_name] = param_spec

                    # Process request body parameters
                    if "requestBody" in method_data:
                        request_body = method_data["requestBody"]
                        request_body_required = request_body.get("required", False)

                        for content_type, content_data in request_body["content"].items():
                            schema = content_data.get("schema", {})

                            # Handle different schema types
                            if schema.get("type") == "object" and "properties" in schema:
                                # Object with properties
                                required_props = schema.get("required", [])

                                for prop_name, prop_schema in schema["properties"].items():
                                    try:
                                        # Extract property type
                                        prop_type = extract_type_from_schema(prop_schema)

                                        # Extract description
                                        prop_description = prop_schema.get("description", "")

                                        # Extract enum values if present
                                        enum_values = prop_schema.get("enum", None)

                                        # Extract constraints
                                        constraints = extract_constraints(prop_schema)

                                        # Create parameter spec
                                        param_spec = {
                                            "_type": "body",
                                            "required": prop_name in required_props,
                                            "type": prop_type,
                                            "description": prop_description,
                                        }

                                        # Add enum values if present
                                        if enum_values:
                                            param_spec["enum"] = enum_values

                                        # Add constraints if present
                                        if constraints:
                                            param_spec.update(constraints)

                                        # Handle parameter name collision
                                        if prop_name in parameters:
                                            parameters[prop_name + "_body"] = param_spec
                                        else:
                                            parameters[prop_name] = param_spec
                                    except Exception as e:
                                        logging.warning(f"Error parsing property {prop_name}: {e}")
                            elif schema.get("type") == "array":
                                # Array type
                                items_schema = schema.get("items", {})
                                param_spec = {
                                    "_type": "body",
                                    "required": request_body_required,
                                    "type": "array",
                                    "items": extract_type_from_schema(items_schema),
                                    "description": schema.get("description", ""),
                                }

                                # Use a generic name for the array parameter
                                array_param_name = "items"
                                if array_param_name in parameters:
                                    parameters[array_param_name + "_body"] = param_spec
                                else:
                                    parameters[array_param_name] = param_spec
                            else:
                                # Simple type or reference
                                param_spec = {
                                    "_type": "body",
                                    "required": request_body_required,
                                    "type": extract_type_from_schema(schema),
                                    "description": schema.get("description", ""),
                                }

                                # Use a generic name for the body parameter
                                body_param_name = "body"
                                if body_param_name in parameters:
                                    parameters[body_param_name + "_data"] = param_spec
                                else:
                                    parameters[body_param_name] = param_spec

                    # Extract response information
                    responses = {}
                    for status_code, response_data in method_data.get("responses", {}).items():
                        response_info = {
                            "description": response_data.get("description", ""),
                        }

                        # Extract response content if available
                        if "content" in response_data:
                            for content_type, content_data in response_data["content"].items():
                                response_schema = content_data.get("schema", {})
                                response_info["content_type"] = content_type
                                response_info["schema"] = extract_type_from_schema(response_schema)
                                break  # Just use the first content type for now

                        responses[status_code] = response_info

                    # Create the tool entry
                    operation_id = method_data.get("operationId")
                    if not operation_id:
                        # Generate an operation ID if not provided
                        operation_id = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"

                    tools[operation_id] = {
                        "path": path,
                        "method": method,
                        "summary": method_data.get("summary", ""),
                        "description": method_data.get("description", ""),
                        "parameters": parameters,
                        "responses": responses,
                        "tags": method_data.get("tags", []),
                        "deprecated": method_data.get("deprecated", False),
                    }

                    # Add security requirements if present
                    if "security" in method_data:
                        tools[operation_id]["security"] = method_data["security"]

                except KeyError as e:
                    logging.error(f"Error parsing {path} {method}: {e}", exc_info=True)
                except Exception as e:
                    logging.error(f"Unexpected error parsing {path} {method}: {e}", exc_info=True)

    return tools


def extract_type_from_schema(schema: Dict[str, Any]) -> Union[str, List[str], Dict[str, Any]]:
    """
    Extract type information from a schema object.

    Args:
        schema: The schema object

    Returns:
        The extracted type information
    """
    if not schema:
        return "object"  # Default to object if no schema

    # Handle references
    if "$ref" in schema:
        ref_path = schema["$ref"]
        # Just return the reference name for now
        # In a more complete implementation, we would resolve the reference
        return ref_path.split("/")[-1]

    # Handle anyOf, oneOf, allOf
    if "anyOf" in schema:
        return [extract_type_from_schema(s) for s in schema["anyOf"] if s.get("type") != "null"]
    if "oneOf" in schema:
        return [extract_type_from_schema(s) for s in schema["oneOf"]]
    if "allOf" in schema:
        # For allOf, we'd ideally merge the schemas, but for simplicity just return the first one
        if schema["allOf"]:
            return extract_type_from_schema(schema["allOf"][0])
        return "object"

    # Handle array type
    if schema.get("type") == "array" and "items" in schema:
        return {"type": "array", "items": extract_type_from_schema(schema["items"])}

    # Handle object type with properties
    if schema.get("type") == "object" and "properties" in schema:
        properties = {}
        for prop_name, prop_schema in schema["properties"].items():
            properties[prop_name] = extract_type_from_schema(prop_schema)

        return {"type": "object", "properties": properties, "required": schema.get("required", [])}

    # Handle simple types
    if "type" in schema:
        return schema["type"]

    # Default fallback
    return "object"


def extract_constraints(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract validation constraints from a schema object.

    Args:
        schema: The schema object

    Returns:
        A dictionary of constraints
    """
    constraints = {}

    # String constraints
    if schema.get("type") == "string":
        if "minLength" in schema:
            constraints["minLength"] = schema["minLength"]
        if "maxLength" in schema:
            constraints["maxLength"] = schema["maxLength"]
        if "pattern" in schema:
            constraints["pattern"] = schema["pattern"]
        if "format" in schema:
            constraints["format"] = schema["format"]

    # Numeric constraints
    if schema.get("type") in ["integer", "number"]:
        if "minimum" in schema:
            constraints["minimum"] = schema["minimum"]
        if "maximum" in schema:
            constraints["maximum"] = schema["maximum"]
        if "exclusiveMinimum" in schema:
            constraints["exclusiveMinimum"] = schema["exclusiveMinimum"]
        if "exclusiveMaximum" in schema:
            constraints["exclusiveMaximum"] = schema["exclusiveMaximum"]
        if "multipleOf" in schema:
            constraints["multipleOf"] = schema["multipleOf"]

    # Array constraints
    if schema.get("type") == "array":
        if "minItems" in schema:
            constraints["minItems"] = schema["minItems"]
        if "maxItems" in schema:
            constraints["maxItems"] = schema["maxItems"]
        if "uniqueItems" in schema:
            constraints["uniqueItems"] = schema["uniqueItems"]

    # Object constraints
    if schema.get("type") == "object":
        if "minProperties" in schema:
            constraints["minProperties"] = schema["minProperties"]
        if "maxProperties" in schema:
            constraints["maxProperties"] = schema["maxProperties"]

    return constraints
