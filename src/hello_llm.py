import argparse

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI

from src.models.config import Settings
from src.tracing import configure_tracing


def call_deepseek(prompt: str, api_key: str) -> str:
    """Call DeepSeek V3 via the OpenAI-compatible API (no tracing)."""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    return response.choices[0].message.content or ""


def call_deepseek_traced(prompt: str, api_key: str) -> str:
    """Call DeepSeek V3 via LangChain ChatModel (auto-traced by LangSmith)."""
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,  # type: ignore[arg-type]
        base_url="https://api.deepseek.com",
        max_completion_tokens=512,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return str(response.content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hello-world LLM call to DeepSeek V3")
    parser.add_argument("--prompt", default="What is LangGraph? Answer in one sentence.")
    parser.add_argument(
        "--traced", action="store_true", help="Use LangChain ChatModel with LangSmith tracing"
    )
    args = parser.parse_args()

    settings = Settings()  # type: ignore[call-arg]

    if args.traced:
        configure_tracing(settings)
        result = call_deepseek_traced(args.prompt, settings.deepseek_api_key)
    else:
        result = call_deepseek(args.prompt, settings.deepseek_api_key)

    print(f"Response:\n{result}")


if __name__ == "__main__":
    main()
