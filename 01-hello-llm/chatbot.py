"""A small, inspectable chat client for Project 1."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol


class ChatError(RuntimeError):
    """Base class for errors the CLI can explain without a traceback."""


class AuthenticationFailure(ChatError):
    pass


class RateLimitFailure(ChatError):
    pass


class NetworkFailure(ChatError):
    pass


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
        )


@dataclass(frozen=True)
class Reply:
    text: str
    usage: Usage


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]], temperature: float) -> Reply: ...


def estimate_cost(
    usage: Usage, input_price_per_million: float, output_price_per_million: float
) -> float:
    """Return an estimate; provider invoices remain the source of truth."""
    return (
        usage.input_tokens * input_price_per_million
        + usage.output_tokens * output_price_per_million
    ) / 1_000_000


def _rough_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class MockClient:
    """Deterministic local stand-in used by demos and tests."""

    def __init__(self, failure: str | None = None) -> None:
        self.failure = failure
        self.calls = 0
        self.seen_messages: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]], temperature: float) -> Reply:
        self.calls += 1
        self.seen_messages.append([message.copy() for message in messages])
        failures = {
            "auth": AuthenticationFailure("Authentication failed. Check OPENAI_API_KEY."),
            "rate": RateLimitFailure("Rate limit reached. Wait briefly, then retry."),
            "network": NetworkFailure("Network request failed. Check your connection."),
        }
        if self.failure in failures:
            raise failures[self.failure]

        latest = messages[-1]["content"]
        text = f"Study-buddy reply: {latest}"
        if "what is my name" in latest.lower():
            prior = " ".join(
                message["content"] for message in messages[:-1] if message["role"] == "user"
            )
            match = re.search(r"my name is\s+([A-Za-z'-]+)", prior, re.IGNORECASE)
            text = f"Your name is {match.group(1)}." if match else "You have not told me your name."
        prompt_text = " ".join(message["content"] for message in messages)
        return Reply(text, Usage(_rough_tokens(prompt_text), _rough_tokens(text)))


class OpenAIClient:
    """Thin official-SDK adapter. Importing is delayed so mock mode is dependency-light."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        if not api_key:
            raise AuthenticationFailure("OPENAI_API_KEY is missing. Copy .env.example to .env.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on local installation
            raise ChatError("Install dependencies with: pip install -r requirements.txt") from exc
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, messages: list[dict[str, str]], temperature: float) -> Reply:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=300,
            )
        except Exception as exc:  # SDK exception classes vary by installed release
            name = type(exc).__name__.lower()
            if "authentication" in name or "permission" in name:
                raise AuthenticationFailure("Authentication failed. Check OPENAI_API_KEY.") from exc
            if "ratelimit" in name or "rate_limit" in name:
                raise RateLimitFailure("Rate limit reached. Wait briefly, then retry.") from exc
            if "connection" in name or "timeout" in name:
                raise NetworkFailure("Network request failed. Check your connection.") from exc
            raise ChatError(f"The model request failed: {type(exc).__name__}") from exc
        usage = response.usage
        return Reply(
            response.choices[0].message.content or "",
            Usage(usage.prompt_tokens or 0, usage.completion_tokens or 0),
        )


class ChatSession:
    def __init__(
        self,
        client: ChatClient,
        system_prompt: str,
        temperature: float = 0.3,
        max_pairs: int = 6,
        input_price: float = 0.40,
        output_price: float = 1.60,
    ) -> None:
        if max_pairs < 1:
            raise ValueError("max_pairs must be at least 1")
        self.client = client
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_pairs = max_pairs
        self.input_price = input_price
        self.output_price = output_price
        self.messages = [{"role": "system", "content": system_prompt}]
        self.total_usage = Usage()
        self.trimmed_pairs = 0

    def _trim_before_call(self) -> None:
        # Keep the system message and newest complete pairs plus the current user message.
        while len(self.messages) > 1 + (self.max_pairs * 2 - 1):
            del self.messages[1:3]
            self.trimmed_pairs += 1

    def send(self, user_text: str) -> Reply:
        self.messages.append({"role": "user", "content": user_text})
        self._trim_before_call()
        try:
            reply = self.client.complete(self.messages, self.temperature)
        except ChatError:
            self.messages.pop()  # failed turns should not become remembered conversation
            raise
        self.messages.append({"role": "assistant", "content": reply.text})
        self.total_usage = self.total_usage + reply.usage
        return reply

    @property
    def estimated_cost(self) -> float:
        return estimate_cost(self.total_usage, self.input_price, self.output_price)


def load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines without adding a runtime dependency."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def chat_loop(
    session: ChatSession,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    output_fn(f"Persona: {session.system_prompt}")
    while True:
        user_text = input_fn("You: ").strip()
        if user_text.lower() in {"quit", "exit"}:
            output_fn("Session ended.")
            return
        if not user_text:
            continue
        try:
            reply = session.send(user_text)
        except ChatError as exc:
            output_fn(f"Could not get a response: {exc}")
            continue
        output_fn(f"Bot: {reply.text}")
        output_fn(
            f"Usage: in={reply.usage.input_tokens}, out={reply.usage.output_tokens}; "
            f"session estimate=${session.estimated_cost:.6f}"
        )
        if session.trimmed_pairs:
            output_fn(f"History notice: removed {session.trimmed_pairs} oldest pair(s).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A direct-SDK command-line chatbot")
    parser.add_argument("--mock", action="store_true", help="use deterministic local replies")
    parser.add_argument("--mock-error", choices=["auth", "rate", "network"])
    parser.add_argument("--once", metavar="TEXT", help="make one call and exit")
    parser.add_argument(
        "--persona",
        default="You are a patient study buddy for introductory statistics.",
    )
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-pairs", type=int, default=6)
    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    mock = args.mock or os.getenv("MOCK_LLM") == "1"
    try:
        client: ChatClient = (
            MockClient(args.mock_error)
            if mock
            else OpenAIClient(
                os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                os.getenv("OPENAI_API_KEY"),
            )
        )
    except ChatError as exc:
        print(f"Configuration error: {exc}")
        return 2
    session = ChatSession(
        client,
        args.persona,
        temperature=args.temperature,
        max_pairs=args.max_pairs,
        input_price=float(os.getenv("INPUT_COST_PER_MILLION", "0.40")),
        output_price=float(os.getenv("OUTPUT_COST_PER_MILLION", "1.60")),
    )
    if args.once is not None:
        try:
            reply = session.send(args.once)
        except ChatError as exc:
            print(f"Could not get a response: {exc}")
            return 2
        print(reply.text)
        print(
            f"Usage: in={reply.usage.input_tokens}, out={reply.usage.output_tokens}; "
            f"session estimate=${session.estimated_cost:.6f}"
        )
        return 0
    chat_loop(session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

