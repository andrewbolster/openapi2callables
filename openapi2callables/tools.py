
import abc
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Set
import requests
import logging

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
    Class instance for executing remote API calls as simple Callables
    """

    base_url: str = None
    path: str = None
    method: str = "get"
    responses: Dict[str, Any] = field(default_factory=dict, repr=False)
    service_name: str | None = None
    access_token_name: str | None = None
    access_token_type: str | None = None
    access_token: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if "API" not in self.tags:
            self.tags.add("API")

        if self.service_name is None:
            self.service_name = self.__class__.__name__

        if self.access_token_name is not None and self.access_token_name not in self.parameters:
            # If no access token is provided, set it to the settings value to be called at runtime
            if self.access_token_type is None:
                self.access_token_type = "virtual"

            self.parameters[self.access_token_name] = {
                "_type": self.access_token_type,
                "type": "str",
                "required": self.access_token is not None,
                "description": "The API token for the {self.service_name} API",
            }

        if self.access_token_name is not None:
            # Need to update the description of the parameter for the system to know it will be provided at runtime
            ## TODO Make this a templated/configured/versioned prompt
            tail_prompt = " (provided by the tool runner at execution time, NEVER ask a user for this!)"
            if not self.parameters[self.access_token_name]["description"].endswith(tail_prompt):
                self.parameters[self.access_token_name]["description"] += tail_prompt

    @property
    def requires_auth(self):
        """
        Check if the tool requires authentication by checking the tags
        """
        if self.access_token_name is not None:
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

    def __call__(self, client=requests.request, *args, **kwds):
        logging.info(f"Calling {self.operationId} with {kwds}")
        params = {}
        body = {}
        path = self.path
        headers = {}
        # To recover from the _body naming convention in parse_spec we need to identify
        # we add a 'virtual' kwds key for each body parameter
        kwds_list = list(kwds.items())
        # New virtual kwargs will be kwd_body for each kwd in kwds that appears in parameters
        shadowed_keys = {k: k[:-5] for k in self.parameters.keys() if k.endswith("_body")}

        if shadowed_keys:
            for key, kwd in shadowed_keys.items():
                kwds_list.append((key, kwds[kwd]))  # so this becomes {root_body: value_of_root}

        for k, v in kwds_list:
            if k not in self.parameters:
                raise ValueError(f"Unknown parameter: {k}, available parameters: {self.parameters.keys()}")
            if self.parameters[k]["_type"] == "body":
                if k.endswith("_body"):
                    k = k[:-5]
                body[k] = v
            if self.parameters[k]["_type"] == "path":
                path = path.replace(f"{{{k}}}", str(v))
            if self.parameters[k]["_type"] == "query":
                params[k] = v
            if self.parameters[k]["_type"] == "header":
                headers[k] = v

        try:
            response = client(
                self.method,
                f"{self.base_url}{path}",
                params=params,
                json=body,
                headers=headers,
            )

            if hasattr(response, "json"):  # requests
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logging.error(f"Error decoding JSON response: {response.text}", exc_info=True)
                    return response.text
                except Exception as e:
                    logging.error(f"Error processing response: {e}, from {response.text}", exc_info=True)
                    return e
            else:  # httpx or otherwise
                return response.content
        except Exception as e:
            logging.error(f"Error making request: {e}", exc_info=True)
            return e
