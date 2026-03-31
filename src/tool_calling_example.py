import argparse
import json

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from openai.types.chat.chat_completion_message_function_tool_call import (
    ChatCompletionMessageFunctionToolCall,
)

from src.models.config import Settings

# --- Step 1: Define the tool schema ---
# The LLM reads this JSON Schema to know what tools are available.
# Think of it as a WSDL / OpenAPI spec for the function.

CALCULATOR_TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a basic arithmetic expression. Use this for any math.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python arithmetic expression, e.g. '(3 + 5) * 12'",
                }
            },
            "required": ["expression"],
        },
    },
}


# --- Step 2: Implement the tool function ---


def calculate(expression: str) -> float:
    """Safely evaluate an arithmetic expression.

    Uses eval() with builtins disabled for this learning example.
    Production code should use a proper math parser (e.g. sympy).
    """
    allowed_names: dict[str, object] = {}
    # Security: __builtins__={} blocks access to import, open, exec, etc.
    return float(eval(expression, {"__builtins__": {}}, allowed_names))  # noqa: S307


# --- Step 3: Agentic loop ---
# Send prompt → LLM returns tool call → execute tool → send result back → get final answer


def run_with_tools(user_question: str, api_key: str, max_rounds: int = 5) -> str:
    """Run a tool-calling loop with DeepSeek.

    The LLM may need multiple tool calls to solve a problem (e.g. breaking
    a complex expression into steps). We loop until the LLM stops calling
    tools or we hit max_rounds.
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": user_question},
    ]

    for round_num in range(1, max_rounds + 1):
        response = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=512,
            tools=[CALCULATOR_TOOL],
            messages=messages,
        )

        assistant_message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        print(f"[Round {round_num}] Finish reason: {finish_reason}")

        # If LLM is done (no tool call), return the text response
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # Process each tool call
        messages.append(assistant_message)  # type: ignore[arg-type]
        for tool_call in assistant_message.tool_calls:
            assert isinstance(tool_call, ChatCompletionMessageFunctionToolCall)
            tool_args = json.loads(tool_call.function.arguments)
            print(f"  Tool '{tool_call.function.name}' called with: {tool_args}")

            tool_result = calculate(tool_args["expression"])
            print(f"  Result: {tool_result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                }
            )

    return "Max rounds reached without a final answer."


def main() -> None:
    parser = argparse.ArgumentParser(description="Tool calling example with calculator")
    parser.add_argument("--question", default="What is (123 * 456) + 789?")
    args = parser.parse_args()

    settings = Settings()  # type: ignore[call-arg]
    answer = run_with_tools(args.question, settings.deepseek_api_key)
    print(f"\nFinal answer: {answer}")


if __name__ == "__main__":
    main()
