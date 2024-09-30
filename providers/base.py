from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract class for integrating different LLM providers."""

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate a response from the LLM. Each provider must implement this method.

        Args:
            prompt (str): The input prompt for the model.
            kwargs (dict): Additional provider-specific arguments.

        Returns:
            str: The response from the LLM.
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """
        Retrieve model information (e.g., model name, version).

        Returns:
            dict: Information about the model.
        """
        pass
