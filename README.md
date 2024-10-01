# LLM Assistant Framework

LLM Assistant Framework is an open-source Python library for building AI assistants using various Large Language Models (LLMs). Inspired by OpenAI's Assistants API, this framework is designed to be flexible, easily adoptable, and compatible with various LLMs.

## Key Features

- Easy-to-use API for creating and managing AI assistants
- Flexible integration with custom LLM providers
- Thread-based conversation management
- Asynchronous execution of assistant runs
- Customizable function calling with type-safe implementations
- Support for multiple assistants in a single thread
- Fine-grained control over assistant behavior and model parameters
- Robust error handling and exception management
- Extensible architecture for adding new tools and capabilities

## TODO

The LLM Assistant Framework is an ongoing project, and there are several features and improvements planned for future releases:

- [ ] Adding more tools: Expand the library of built-in tools for common tasks.
- [ ] Adding streaming: Implement support for streaming responses from LLMs.
- [ ] Adding JSON Schema support: Enhance function definitions with JSON Schema for better type validation.
- [ ] Implement caching mechanisms: Add caching for LLM responses to improve performance and reduce API calls.
- [ ] Enhance error handling: Provide more granular error types and improve error messages for better debugging.
- [ ] Add support for file attachments: Allow file uploads and downloads in conversations.
- [ ] Implement conversation memory management: Add features to manage long-term memory and context for assistants.
- [ ] Improve documentation: Expand and enhance the documentation with more examples and use cases.
- [ ] Implement logging and monitoring: Add comprehensive logging and monitoring features for better observability.

## Installation

You can install the LLM Assistant Framework using pip:

```bash
pip install assinstants
```

For developers who want to contribute or modify the framework:

```bash
git clone https://github.com/lahfir/assinstants.git
cd assinstants
pip install -e .
```

## Project Structure

```
assinstants/
├── core/
│   ├── __init__.py
│   ├── assistant_manager.py
│   ├── thread_manager.py
│   └── run_manager.py
├── models/
│   ├── __init__.py
│   ├── assistant.py
│   ├── base.py
│   ├── function.py
│   ��── message.py
│   ├── run.py
│   ├── shared.py
│   ├── thread.py
│   └── tool.py
└── utils/
    └── exceptions.py
```

## Setup and Execution Flow Diagram

![Setup and Execution Flow Diagram](./assinstants/Images/Setup%20and%20Execution%20Flow%20Diagram.png)

## Run Execution and Tool Usage Diagram

![Run Execution and Tool Usage Diagram](./assinstants/Images/Run%20Execution%20and%20Tool%20Usage%20Flowchart.png)

## Asynchronous Operation Diagram

![Asynchronous Operation Diagram](./assinstants/Images/Asynchronous%20Operation%20Diagram.png)

## Quick Start Guide

Here's a basic example of how to use the LLM Assistant Framework:

```python
import asyncio
import aiohttp
from assinstants import AssistantManager, ThreadManager, RunManager
from assinstants.models.function import (
    FunctionDefinition,
    FunctionParameter,
)
from assinstants.models.tool import Tool, FunctionTool
from assinstants.utils.exceptions import (
    RunExecutionError,
    FunctionNotFoundError,
    FunctionExecutionError,
)
import logging

logging.basicConfig(level=logging.DEBUG)

OPENWEATHERMAP_API_KEY = ""


async def custom_llm_function(model: str, prompt: str, **kwargs) -> str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, **kwargs},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                result = await response.json()
                return result.get("response", "")
        except asyncio.TimeoutError:
            return "LLM request timed out"
        except Exception as e:
            return f"Error: {str(e)}"


async def get_weather(city: str, country_code: str) -> dict:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country_code}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            print(f"Weather data: {data}")
            if response.status == 200:
                logging.debug(f"Weather data: {data}")
                return {
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                }
            else:
                raise Exception(
                    f"Error fetching weather data for {city}, {country_code}: {data.get('message', 'Unknown error')}"
                )


async def main():
    assistant_manager = AssistantManager()
    thread_manager = ThreadManager()
    run_manager = RunManager(assistant_manager, thread_manager)

    tools = [
        Tool(
            tool=FunctionTool(
                function=FunctionDefinition(
                    name="get_weather",
                    description="Get current weather for a city",
                    parameters={
                        "city": FunctionParameter(
                            type="string", description="City name"
                        ),
                        "country_code": FunctionParameter(
                            type="string", description="Two-letter country code"
                        ),
                    },
                    implementation=get_weather,
                )
            )
        )
    ]

    assistant = await assistant_manager.create_assistant(
        name="Weather Assistant",
        instructions="""You are a weather assistant.""",
        model="llama3",
        custom_llm_function=custom_llm_function,
        tools=tools,
        temperature=0.7,
    )

    thread = await thread_manager.create_thread()
    await thread_manager.add_assistant_to_thread(thread.id, assistant)

    print("Welcome to the Weather Assistant! Type 'exit' to end the conversation.")

    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            print("Thank you for using the Weather Assistant. Goodbye!")
            break

        await thread_manager.add_message(thread.id, "user", user_query)

        try:
            run = await run_manager.create_and_execute_run(thread.id)
            messages = await thread_manager.get_messages(thread.id)
            final_answer = messages[-1].content if messages else "No response generated"
            print(f"Assistant: {final_answer}")
        except RunExecutionError as e:
            print(f"Run execution error: {str(e)}")
        except FunctionNotFoundError as e:
            print(f"Function not found error: {str(e)}")
        except FunctionExecutionError as e:
            print(f"Function execution error: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Core Components

The LLM Assistant Framework consists of four main components:

1. **Assistants**: AI models with specific instructions and capabilities.
2. **Threads**: Conversations or contexts for interactions.
3. **Messages**: Individual pieces of communication within a thread.
4. **Runs**: Executions of an assistant on a specific thread.

The framework provides three main manager classes to interact with these components:

- `AssistantManager`: For creating and managing assistants
- `ThreadManager`: For managing conversation threads and messages
- `RunManager`: For executing and managing assistant runs

## Advanced Usage

### Using Multiple Assistants in a Thread

```python
async def main():
    assistant1 = await assistant_manager.create_assistant(name="Math Tutor", ...)
    assistant2 = await assistant_manager.create_assistant(name="Writing Assistant", ...)

    thread = await thread_manager.create_thread()
    await thread_manager.add_assistant_to_thread(thread.id, assistant1)
    await thread_manager.add_assistant_to_thread(thread.id, assistant2)

    await thread_manager.add_message(thread.id, "user", "Can you help me with my math homework?")
    run = await run_manager.create_and_execute_run(thread.id)

    await thread_manager.add_message(thread.id, "user", "Now, can you help me write an essay about the math concepts I just learned?")
    run = await run_manager.create_and_execute_run(thread.id)
```

### Defining Custom Functions

```python
from assinstants.models.function import FunctionDefinition, FunctionParameter
from assinstants.models.tool import Tool, FunctionTool

def calculate_square_root(x: float) -> float:
    return x ** 0.5

tools = [
    Tool(
        tool=FunctionTool(
            function=FunctionDefinition(
                name="calculate_square_root",
                description="Calculate the square root of a number",
                parameters={
                    "x": FunctionParameter(
                        type="number",
                        description="The number to calculate the square root of"
                    )
                },
                implementation=calculate_square_root
            )
        )
    )
]

assistant = await assistant_manager.create_assistant(
    name="Math Assistant",
    tools=tools,
    ...
)
```

### Error Handling

```python
from assinstants.utils.exceptions import AssistantNotFoundError, ThreadNotFoundError

try:
    assistant = await assistant_manager.get_assistant("non_existent_id")
except AssistantNotFoundError as e:
    print(f"Error: {e}")

try:
    thread = await thread_manager.get_thread("non_existent_id")
except ThreadNotFoundError as e:
    print(f"Error: {e}")
```

## Customization

### Integrating Custom LLM Providers

To integrate a custom LLM provider, create a function that implements the LLM API call and pass it to the `create_assistant` method:

```python
async def my_custom_llm_function(model: str, prompt: str, **kwargs):
    # Implement your custom LLM API call here
    return "LLM response"

assistant = await assistant_manager.create_assistant(
    name="Custom Assistant",
    custom_llm_function=my_custom_llm_function,
    ...
)
```

### Adding New Tools and Functions

To add new tools or functions to assistants, create `FunctionDefinition` objects with the necessary parameters and logic, then pass them to the assistant during creation:

```python
from assinstants.models.function import FunctionDefinition, FunctionParameter
from assinstants.models.tool import Tool, FunctionTool

def my_custom_function(param1: str, param2: float) -> str:
    # Your function logic here
    return f"Result: {param1}, {param2}"

tools = [
    Tool(
        tool=FunctionTool(
            function=FunctionDefinition(
                name="my_custom_function",
                description="Description of what the function does",
                parameters={
                    "param1": FunctionParameter(
                        type="string", description="Description of param1"
                    ),
                    "param2": FunctionParameter(
                        type="number", description="Description of param2"
                    ),
                },
                implementation=my_custom_function,
            )
        )
    )
]

assistant = await assistant_manager.create_assistant(
    name="Custom Assistant",
    tools=tools,
    ...
)
```

## Error Handling

The LLM Assistant Framework provides several exception classes for handling specific errors:

- `AssistantNotFoundError`: Raised when an assistant is not found
- `ThreadNotFoundError`: Raised when a thread is not found
- `InvalidProviderError`: Raised when an invalid LLM provider is specified
- `RunExecutionError`: Raised when there's an error during run execution
- `FunctionNotFoundError`: Raised when a function is not found
- `FunctionExecutionError`: Raised when there's an error executing a function

Use these exceptions in try-except blocks to handle specific error cases in your application.

## Contributing

I welcome contributions from the community to help implement these features and improve the framework. If you're interested in working on any of these items, please check our issues page or open a new issue to discuss your ideas:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and write tests if applicable
4. Ensure all tests pass
5. Submit a pull request with a clear description of your changes

For bug reports or feature requests, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Version Management

For detailed information on our version management and branching strategy, please refer to the [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) file. This document outlines our approach to semantic versioning, branching strategy, and release process.

## Contributing

I welcome contributions from the community to help implement these features and improve the framework. If you're interested in working on any of these items, please check our issues page or open a new issue to discuss your ideas:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and write tests if applicable
4. Ensure all tests pass
5. Submit a pull request with a clear description of your changes

For bug reports or feature requests, please open an issue on the GitHub repository.
