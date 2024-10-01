import json
import logging
from typing import List, Dict, Any, Union
from ..models.run import Run, RunStatus
from ..models.shared import StepDetails, FunctionCall
from ..models.assistant import Assistant
from ..models.message import Message
from ..core.assistant_manager import AssistantManager
from ..core.thread_manager import ThreadManager
from datetime import datetime, timezone
from ..utils.exceptions import (
    RunExecutionError,
    FunctionNotFoundError,
    FunctionExecutionError,
)
from ..models.tool import FunctionTool
from ..models.function import FunctionParameter
from ..models.tool import Tool
from ..utils.logging_utils import log

logger = logging.getLogger(__name__)


class RunManager:
    def __init__(
        self, assistant_manager: AssistantManager, thread_manager: ThreadManager
    ):
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.runs: Dict[str, Run] = {}

    async def create_and_execute_run(self, thread_id: str) -> Run:
        log("THREAD", f"Creating and executing run for thread {thread_id}")
        messages = await self.thread_manager.get_messages(thread_id)
        user_query = next(
            (m.content for m in reversed(messages) if m.role == "user"), None
        )
        if not user_query:
            log("ERROR", "No user message found in the thread", logging.ERROR)
            raise ValueError("No user message found in the thread")

        log("THREAD", f"User query: {user_query}")
        thread = await self.thread_manager.get_thread(thread_id)
        run = Run(thread_id=thread_id, assistant_id=thread.assistants[0].id)
        self.runs[run.id] = run
        return await self.execute_run(
            run.id, user_query, thread.assistants, messages[-5:]
        )

    async def execute_run(
        self,
        run_id: str,
        user_query: str,
        assistants: List[Assistant],
        messages: List[Message],
    ) -> Run:
        log("THREAD", f"Executing run {run_id}")
        run = self.runs.get(run_id)
        if not run:
            log("ERROR", f"Invalid run_id: {run_id}", logging.ERROR)
            raise ValueError("Invalid run_id")

        run.status = RunStatus.IN_PROGRESS
        run.started_at = datetime.now(timezone.utc)
        log("THREAD", f"Run {run_id} started at {run.started_at}")

        try:
            serializable_messages = self._serialize_messages(messages)
            process_result = await self._process_query(
                user_query, serializable_messages, assistants
            )
            run.assistant_id = process_result["assistant_id"]
            run.steps = process_result["steps"]

            selected_assistant = next(
                (a for a in assistants if a.id == run.assistant_id),
                assistants[0],
            )
            log("ASSISTANT", f"Selected assistant: {selected_assistant.name}")

            function_results = []
            errors = []
            for step in run.steps:
                log("STEP", f"Executing step {step.step_number}: {step.description}")
                try:
                    step_results = await self._execute_step(run.assistant_id, step)
                    function_results.extend(step_results)
                    step.results = step_results
                except FunctionExecutionError as e:
                    log("ERROR", f"Function execution error: {str(e)}", logging.ERROR)
                    errors.append(str(e))

            final_response = await self._generate_final_response(
                selected_assistant,
                user_query,
                function_results,
                serializable_messages,
                errors,
            )

            # Extract the actual response from the JSON
            try:
                response_json = json.loads(final_response)
                if isinstance(response_json, dict) and "response" in response_json:
                    extracted_response = response_json["response"].strip()
                else:
                    extracted_response = final_response.strip()
            except json.JSONDecodeError:
                extracted_response = final_response.strip()

            log("THREAD", f"Final response: {extracted_response}")
            await self.thread_manager.add_message(
                run.thread_id, "assistant", extracted_response, run.assistant_id
            )

            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            log("THREAD", f"Run {run_id} completed at {run.completed_at}")
            return run

        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = str(e)
            log("ERROR", f"Run execution failed: {str(e)}", logging.ERROR)
            raise RunExecutionError(f"Run execution failed: {str(e)}")

    def _serialize_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        return [
            {
                "role": message.role,
                "content": message.content,
                "created_at": (
                    message.created_at.isoformat() if message.created_at else None
                ),
                "assistant_id": message.assistant_id,
            }
            for message in messages
        ]

    def _serialize_function_parameter(self, param: FunctionParameter) -> Dict[str, Any]:
        return {
            "type": param.type,
            "description": param.description,
            "enum": param.enum,
        }

    def _parse_json_response(self, response: str) -> Union[Dict[str, Any], str]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Attempt to extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end != -1:
                try:
                    extracted_json = response[json_start:json_end]
                    return json.loads(extracted_json)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Failed to extract valid JSON from response: {response}"
                    )
            logger.error(f"No valid JSON found in response: {response}")
            return response.strip()

    async def _process_query(
        self,
        user_query: str,
        messages: List[Dict[str, Any]],
        assistants: List[Assistant],
    ) -> Dict[str, Any]:
        available_functions = [
            {
                "name": tool.tool.function.name,
                "description": tool.tool.function.description,
                "parameters": {
                    name: self._serialize_function_parameter(param)
                    for name, param in tool.tool.function.parameters.items()
                },
            }
            for assistant in assistants
            for tool in assistant.tools
            if isinstance(tool.tool, FunctionTool)
        ]

        prompt = f"""
Analyze the following user query and determine the necessary steps to respond:

<user_query>
{user_query}
</user_query>

Recent conversation history:
{self._format_conversation_history(messages[-5:])}

Available assistants and their functions:
{self._format_assistants_and_functions(assistants)}

Task: Determine the steps needed to respond to the user query and select the most appropriate assistant. Use available functions only when required. For general conversation, no function calls are needed.

Your response should be a valid JSON object with the following structure:
{{
    "steps": [
        {{
            "step_number": integer,
            "description": "string",
            "function_calls": [
                {{
                    "name": "string",
                    "arguments": object
                }}
            ]
        }}
    ],
    "selected_assistant_index": integer
}}

Important instructions:
- Respond ONLY with a valid JSON object matching the output format.
- Do not include any text outside the JSON structure.
- Strictly adhere to the function parameters if a function call is needed.
- Always select an appropriate assistant by setting the selected_assistant_index.
- Choose the assistant that has the required functions for the task.
"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await assistants[0].custom_llm_function(
                    assistants[0].model, prompt
                )
                logger.debug(
                    f"Raw LLM response for process_query (attempt {attempt + 1}): {response}"
                )

                # Try to extract JSON from the response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start != -1 and json_end != -1:
                    json_response = response[json_start:json_end]
                    result = json.loads(json_response)
                else:
                    raise json.JSONDecodeError(
                        "No JSON found in the response", response, 0
                    )

                steps = result.get("steps", [])
                selected_assistant_index = result.get("selected_assistant_index")

                if not steps:
                    logger.info("No steps found in LLM response")
                    steps = []

                # Validate function calls
                available_function_names = set(
                    func["name"] for func in available_functions
                )
                steps = [
                    {
                        **step,
                        "function_calls": [
                            call
                            for call in step.get("function_calls", [])
                            if call["name"] in available_function_names
                        ],
                    }
                    for step in steps
                ]
                steps = [step for step in steps if step["function_calls"]]

                selected_assistant = (
                    assistants[selected_assistant_index]
                    if selected_assistant_index is not None
                    and 0 <= selected_assistant_index < len(assistants)
                    else assistants[0]
                )

                return {
                    "assistant_id": selected_assistant.id,
                    "steps": [
                        StepDetails(
                            step_number=step["step_number"],
                            description=step["description"],
                            function_calls=[
                                FunctionCall(**call) for call in step["function_calls"]
                            ],
                        )
                        for step in steps
                    ],
                }

            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as e:
                logger.error(
                    f"Error processing LLM response (attempt {attempt + 1}): {str(e)}"
                )
                if attempt == max_retries - 1:
                    raise ValueError(
                        f"Failed to get a valid response after {max_retries} attempts: {str(e)}"
                    )

        raise ValueError("Unexpected error in _process_query")

    def _format_conversation_history(self, messages: List[Dict[str, Any]]) -> str:
        formatted_history = ""
        for message in messages:
            formatted_history += f"[{message['role']}]: {message['content']}\n"
        return formatted_history

    def _format_available_functions(self, functions: list[Tool]) -> str:
        formatted_functions = ""
        for func in functions:
            formatted_functions += f"Function: {func.tool.function.name}\n"
            formatted_functions += f"Description: {func.tool.function.description}\n"
            formatted_functions += "Parameters:\n"
            for param_name, param_details in func.tool.function.parameters.items():
                formatted_functions += f"  - {param_name}: {param_details.type} - {param_details.description}\n"
            formatted_functions += "\n"
        return formatted_functions

    async def _execute_step(
        self, assistant_id: str, step: StepDetails
    ) -> List[Dict[str, Any]]:
        log("STEP", f"Executing step {step.step_number}: {step.description}")
        results = []
        assistant = await self.assistant_manager.get_assistant(assistant_id)
        if step.function_calls:
            for function_call in step.function_calls:
                log("FUNCTION", f"Executing function: {function_call.name}")
                result = await self._execute_function(assistant, function_call)
                results.append({function_call.name: result})
        return results

    async def _execute_function(
        self, assistant: Assistant, function_call: FunctionCall
    ) -> Any:
        function_tool = next(
            (
                tool.tool.function
                for tool in assistant.tools
                if isinstance(tool.tool, FunctionTool)
                and tool.tool.function.name == function_call.name
            ),
            None,
        )
        if not function_tool:
            log("ERROR", f"Function {function_call.name} not found", logging.ERROR)
            raise FunctionNotFoundError(f"Function {function_call.name} not found")

        try:
            result = await function_tool.implementation(**function_call.arguments)
            log("FUNCTION", f"Function {function_call.name} executed successfully")
            return result
        except Exception as e:
            log(
                "ERROR",
                f"Error executing function {function_call.name}: {str(e)}",
                logging.ERROR,
            )
            raise FunctionExecutionError(
                f"Error executing function {function_call.name}: {str(e)}"
            )

    async def _generate_final_response(
        self,
        selected_assistant: Assistant,
        user_query: str,
        function_results: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        errors: List[str],
    ) -> str:
        logger.info("Generating final response")
        prompt = f"""
Generate a natural, conversational response to the following user query:

<user_query>
{user_query}
</user_query>

Recent conversation history:
{self._format_conversation_history(messages[-5:])}

Function results:
{self._format_function_results(function_results)}

Errors encountered:
{self._format_errors(errors)}

Assistant Instructions:
{selected_assistant.instructions}

Available functions:
{self._format_available_functions(selected_assistant.tools)}

Task: Generate a natural, conversational response to the user's query based on the conversation history, function results, and any errors that occurred. If there were errors, acknowledge them in your response. Use the available functions if necessary.

Your response should be a valid JSON object with the following structure:
{{
    "response": "Your generated response as a string",
    "function_calls": [
        {{
            "name": "function_name",
            "arguments": {{}}
        }}
    ]
}}

Important instructions:
- Respond ONLY with a valid JSON object matching the output format.
- Do not include any text outside the JSON structure.
- Incorporate relevant information from the function results and conversation history.
- If there were errors, acknowledge them in a user-friendly manner.
- Keep the tone conversational and natural.
- Use the available functions if they are relevant to the user's query.
- If no functions are needed, provide an empty list for "function_calls".
"""
        logger.debug(f"Final response prompt: {prompt}")

        response = await selected_assistant.custom_llm_function(
            selected_assistant.model, prompt
        )
        logger.debug(f"Raw LLM response for final response: {response}")

        parsed_response = self._parse_json_response(response)
        if isinstance(parsed_response, dict) and "response" in parsed_response:
            # Execute any function calls
            if (
                "function_calls" in parsed_response
                and parsed_response["function_calls"]
            ):
                for call in parsed_response["function_calls"]:
                    if call.get("name"):
                        try:
                            result = await self._execute_function(
                                selected_assistant, FunctionCall(**call)
                            )
                            parsed_response[
                                "response"
                            ] += f"\n\nFunction result: {result}"
                        except Exception as e:
                            parsed_response[
                                "response"
                            ] += f"\n\nError executing function: {str(e)}"

            return parsed_response["response"]
        else:
            logger.warning(
                "LLM response was not in expected JSON format. Using raw response."
            )
            return str(parsed_response)

    def _format_function_results(self, function_results: List[Dict[str, Any]]) -> str:
        formatted_results = ""
        for result in function_results:
            for func_name, func_result in result.items():
                formatted_results += f"Function: {func_name}\n"
                formatted_results += f"Result: {json.dumps(func_result, indent=2)}\n\n"
        return formatted_results or "No function results available."

    def _format_errors(self, errors: List[str]) -> str:
        return "\n".join(errors) if errors else "No errors encountered."

    async def get_run(self, run_id: str) -> Run:
        run = self.runs.get(run_id)
        if run is None:
            raise ValueError(f"Run with id {run_id} not found")
        return run

    def _format_assistants_and_functions(self, assistants: List[Assistant]) -> str:
        formatted_output = ""
        for index, assistant in enumerate(assistants):
            formatted_output += f"Assistant {index}: {assistant.name}\n"
            formatted_output += f"Instructions: {assistant.instructions}\n"
            formatted_output += "Functions:\n"
            for tool in assistant.tools:
                if isinstance(tool.tool, FunctionTool):
                    func = tool.tool.function
                    formatted_output += f"  - {func.name}: {func.description}\n"
                    formatted_output += "    Parameters:\n"
                    for param_name, param in func.parameters.items():
                        formatted_output += (
                            f"      {param_name}: {param.type} - {param.description}\n"
                        )
                        if param.enum:
                            formatted_output += (
                                f"Allowed values: {', '.join(param.enum)}\n"
                            )
            formatted_output += "\n"
        return formatted_output
