import argparse

from openai import OpenAI

from src.models.config import Settings


def call_deepseek(prompt: str, api_key: str) -> str:
    """Call DeepSeek V3 via the OpenAI-compatible API."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Hello-world LLM call to DeepSeek V3")
    parser.add_argument("--prompt", default="What is LangGraph? Answer in one sentence.")
    args = parser.parse_args()

    settings = Settings()  # type: ignore[call-arg]
    result = call_deepseek(args.prompt, settings.deepseek_api_key)
    print(f"Response:\n{result}")


if __name__ == "__main__":
    main()
