import abc
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Set

import requests


@dataclass
class Tool(abc.ABC):
    """
    Abstract Base Class for Tool Calling
    """

    operationId: str
    description: str
    parameters: Dict[str, Any] = field(hash=False, compare=False)
    responses: Dict[str, Any] = field(default_factory=dict, repr=False)
    summary: str = field(default=None, repr=False)
    tags: Set[str] = field(default_factory=set, repr=False)

    def __hash__(self):
        return hash(self.operationId)

    def __post_init__(self):
        if self.summary is not None:
            # prepend the description with the summary
            self.description = f"{self.summary}\n\n{self.description}"

        if isinstance(self.tags, list):
            # Convert tags to a set for consistency
            self.tags = set(self.tags)

    @property
    @abc.abstractmethod
    def requires_auth(self):
        """
        Check if the tool requires authentication
        """
        ...

    @property
    def requires_confirmation(self):
        """
        Check if the tool requires confirmation by checking the tags
        """
        return "requires-confirmation" in self.tags

    @abc.abstractmethod
    def __call__(self, *args, **kwds): ...

    def to_tool_spec(self):
        """
        Express the Tool in a format accepted by the OpenAI API as a 'Tool'

        Execution of the particular tool is the responsibility of the calling client
        """
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


@dataclass
class LocalTool(Tool):
    """
    Class instance for executing client-local functions
    >>> f = LocalTool(operationId='f', description='f', parameters={'x':{'type':"integer", 'description':"the input", 'required'=True}}, func=lambda x: x+1)
    >>> f(1)
    2
    """

    func: Callable = field(hash=False, compare=False, default=lambda x: x)

    def __post_init__(self):
        super().__post_init__()
        if "Local" not in self.tags:
            self.tags.add("Local")

    @property
    def requires_auth(self):
        """
        Check if the tool requires authentication
        """
        return False

    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)


@dataclass
class APITool(Tool):
    """
    Class instance for executing remote API calls as simple Callables.

    Enhanced to handle complex OpenAPI features including:
    - Authentication (API keys, tokens, OAuth)
    - Complex request bodies with nested objects
    - File uploads
    - Custom headers and cookies
    - Response handling with different content types
    - Error handling with status codes
    """

    base_url: str = None
    path: str = None
    method: str = "get"
    responses: Dict[str, Any] = field(default_factory=dict, repr=False)
    service_name: str | None = None
    deprecated: bool = False
    ## Authentication parameters
    access_token_name: str | None = None
    access_token_type: str | None = None
    access_token: str | None = None
    ## Default values for request parameters
    timeout: int = 30
    follow_redirects: bool = True
    retry_count: int = 0
    retry_backoff: float = 1.0
    content_type: str | None = None
    accept: str | None = None
    security_schemes: Dict[str, Dict[str, Any]] = field(default_factory=dict, repr=False)
    cookies: Dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        super().__post_init__()
        if "API" not in self.tags:
            self.tags.add("API")

        if self.service_name is None:
            self.service_name = self.__class__.__name__

        # Handle authentication parameters
        if self.access_token_name is not None and self.access_token_name not in self.parameters:
            # If no access token is provided, set it to the settings value to be called at runtime
            if self.access_token_type is None:
                self.access_token_type = "virtual"

            self.parameters[self.access_token_name] = {
                "_type": self.access_token_type,
                "type": "str",
                "required": self.access_token is not None,
                "description": f"The API token for the {self.service_name} API",
            }

        if self.access_token_name is not None:
            # Need to update the description of the parameter for the system to know it will be provided at runtime
            tail_prompt = " (provided by the tool runner at execution time, NEVER ask a user for this!)"
            if not self.parameters[self.access_token_name]["description"].endswith(tail_prompt):
                self.parameters[self.access_token_name]["description"] += tail_prompt

    @property
    def requires_auth(self):
        """
        Check if the tool requires authentication.
        """
        if self.access_token_name is not None or self.security_schemes:
            return True

        # Check for auth-related parameters
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("_type") in ["header", "cookie"] and any(
                auth_term in param_name.lower() for auth_term in ["api_key", "token", "auth", "key", "secret"]
            ):
                return True

        return False

    def resolve_access_token(self, kwds) -> str:
        """
        Resolve the access token to use for the API request.
        Priority:
        1. self.access_token_name named argument passed at runtime
        2. "access_token" passed set at instantiation
        3. "access_token" set in settings
        4. raise error
        """
        if self.access_token_name in kwds and kwds[self.access_token_name] is not None:
            logging.debug("Using access token from kwds")
            return kwds.pop(self.access_token_name)
        if self.access_token is not None:
            logging.debug(f"Using access token from {self.__class__.__name__}")
            return self.access_token
        raise ValueError(f"No {self.service_name} API key found; cannot make request")

    def validate_parameter_type(self, param_name, param_value, expected_type=None):
        if expected_type is None:
            # Get the expected type from the parameters
            expected_type = self.parameters[param_name]["type"]

        if isinstance(expected_type, list):  # OneOf/AnyOf
            if len(expected_type) == 1:
                expected_type = expected_type[0]
            else:
                # Handle oneOf/anyOf types
                for t in expected_type:
                    if isinstance(t, dict):
                        # This is a complex type, check if the value is a dict
                        if isinstance(param_value, dict):
                            return
                    else:
                        # This is a primitive type, check if the value matches
                        try:
                            self.validate_parameter_type(param_name, param_value, expected_type=t)
                            return
                        except TypeError:
                            continue
                raise TypeError(
                    f"Invalid type for parameter {param_name}: expected one of {expected_type}, got {type(param_value).__name__}"
                )

        if expected_type == "integer":
            expected_type = int
        elif expected_type == "number":
            expected_type = float
        elif expected_type == "string":
            expected_type = str
        elif expected_type == "boolean":
            expected_type = bool
        elif expected_type == "array":
            expected_type = list
        else:
            logging.warning(f"Unknown type for parameter {param_name}: {expected_type}")
            expected_type = eval(expected_type)
        if not isinstance(param_value, expected_type):
            raise TypeError(
                f"Invalid type for parameter {param_name}: expected {expected_type}, got {type(param_value).__name__}"
            )

        return expected_type

    def prepare_request_data(self, kwds):
        """
        Prepare request data from keyword arguments.

        Args:
            kwds: Keyword arguments passed to the tool

        Returns:
            Tuple of (path, params, headers, cookies, body, files)
        """
        params = {}
        body = {}
        path = self.path
        headers = {}
        cookies = self.cookies.copy()
        files = None

        # Process shadowed keys (parameters with _body suffix)
        kwds_list = list(kwds.items())
        shadowed_keys = {k: k[:-5] for k in self.parameters.keys() if k.endswith("_body")}

        if shadowed_keys:
            for key, kwd in shadowed_keys.items():
                if kwd in kwds:
                    kwds_list.append((key, kwds[kwd]))

        # Set default content type if not overridden
        if self.content_type and "Content-Type" not in headers:
            headers["Content-Type"] = self.content_type

        # Set accept header if specified
        if self.accept and "Accept" not in headers:
            headers["Accept"] = self.accept

        # Validate required parameters
        for param_name, param_spec in self.parameters.items():
            param_name = shadowed_keys.get(param_name, param_name)
            if param_spec["required"] and param_name not in kwds:
                raise ValueError(f"Missing required parameter: {param_name}")

        # Validate parameter types
        for param_name, param_value in kwds.items():
            if param_name in self.parameters:
                self.validate_parameter_type(param_name, param_value)

        # Process parameters based on their type
        for k, v in kwds_list:
            if k not in self.parameters:
                logging.warning(f"Unknown parameter: {k}, available parameters: {list(self.parameters.keys())}")
                continue

            param_type = self.parameters[k]["_type"]

            if param_type == "body":
                # Handle body parameters
                if k.endswith("_body"):
                    k = k[:-5]

                # Handle nested objects and arrays
                if isinstance(v, dict) and isinstance(self.parameters[k].get("type"), dict):
                    # This is a complex object, add it directly to the body
                    body[k] = v
                elif isinstance(v, list) and self.parameters[k].get("type") == "array":
                    # This is an array, add it directly to the body
                    body[k] = v
                else:
                    # Simple value
                    body[k] = v
            elif param_type == "path":
                # Handle path parameters
                path = path.replace(f"{{{k}}}", str(v))
            elif param_type == "query":
                # Handle query parameters
                if isinstance(v, list):
                    # Handle array query parameters
                    params[k] = ",".join(str(item) for item in v)
                else:
                    params[k] = v
            elif param_type == "header":
                # Handle header parameters
                headers[k] = v
            elif param_type == "cookie":
                # Handle cookie parameters
                cookies[k] = v
            elif param_type == "formData":
                # Handle form data
                if files is None:
                    files = {}

                if hasattr(v, "read"):
                    # This is a file-like object
                    files[k] = v
                else:
                    # This is a regular form field
                    if files:
                        files[k] = (None, str(v))
                    else:
                        if not body:
                            body = {}
                        body[k] = v

        return path, params, headers, cookies, body, files

    def handle_response(self, response):
        """
        Handle the response from the API.

        Args:
            response: The response object

        Returns:
            The processed response data
        """
        # Check for error status codes
        if hasattr(response, "status_code") and response.status_code >= 400:
            logging.error(f"Error response: {response.status_code} - {response.text}")

            # Try to parse error response
            try:
                error_data = response.json()
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": error_data.get("message", error_data.get("error", response.text)),
                    "data": error_data,
                }
            except json.JSONDecodeError:
                return {"error": True, "status_code": response.status_code, "message": response.text}

        # Process successful response
        if hasattr(response, "json"):
            try:
                return response.json()
            except json.JSONDecodeError:
                content_type = response.headers.get("Content-Type", "")

                if "text/plain" in content_type:
                    return response.text
                elif "text/html" in content_type:
                    return {"content_type": "text/html", "data": response.text}
                else:
                    return response.text
        else:
            # Handle non-requests response objects
            return response.content

    def __call__(self, client=requests.request, *args, **kwds):
        """
        Execute the API call.

        Args:
            client: The HTTP client to use (defaults to requests.request)
            *args: Positional arguments (ignored)
            **kwds: Keyword arguments for the API call

        Returns:
            The processed response from the API
        """
        logging.info(f"Calling {self.operationId} with {kwds}")

        # Prepare request data
        path, params, headers, cookies, body, files = self.prepare_request_data(kwds)

        # Handle authentication if needed
        if self.requires_auth and self.access_token_name:
            try:
                token = self.resolve_access_token(kwds)
                # Determine where to put the token based on access_token_type
                if self.access_token_type == "header":
                    headers["Authorization"] = f"Bearer {token}"
                elif self.access_token_type == "query":
                    params[self.access_token_name] = token
                elif self.access_token_type == "cookie":
                    cookies[self.access_token_name] = token
            except ValueError as e:
                logging.error(f"Authentication error: {e}")
                return {"error": True, "message": str(e)}

        # Determine request data based on content type
        request_kwargs = {
            "params": params,
            "headers": headers,
            "cookies": cookies,
            "timeout": self.timeout,
        }

        if files:
            # If we have files, don't set json parameter
            request_kwargs["files"] = files
            if body:
                request_kwargs["data"] = body
        elif body:
            # If we have a body but no files, use json parameter
            request_kwargs["json"] = body

        # Add follow_redirects for requests compatibility
        if hasattr(client, "__module__") and "requests" in client.__module__:
            request_kwargs["allow_redirects"] = self.follow_redirects

        # Execute request with retry logic
        retry_count = 0
        max_retries = self.retry_count
        backoff = self.retry_backoff

        while True:
            try:
                response = client(self.method, f"{self.base_url}{path}", **request_kwargs)

                return self.handle_response(response)
            except Exception as e:
                logging.error(f"Error making request: {e}", exc_info=True)

                if retry_count < max_retries:
                    retry_count += 1
                    retry_delay = backoff * (2 ** (retry_count - 1))  # Exponential backoff
                    logging.info(f"Retrying in {retry_delay} seconds... (attempt {retry_count}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    return {"error": True, "message": str(e)}
