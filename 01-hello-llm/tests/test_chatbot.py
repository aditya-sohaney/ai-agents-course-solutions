from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from chatbot import (  # noqa: E402
    AuthenticationFailure,
    ChatSession,
    MockClient,
    NetworkFailure,
    RateLimitFailure,
    Usage,
    chat_loop,
    estimate_cost,
)


def make_session(client=None, max_pairs=6):
    return ChatSession(client or MockClient(), "You are a test tutor.", max_pairs=max_pairs)


def test_system_and_user_messages_are_sent():
    client = MockClient()
    make_session(client).send("Hello")
    assert [message["role"] for message in client.seen_messages[0]] == ["system", "user"]


def test_history_is_resent_on_second_turn():
    client = MockClient()
    session = make_session(client)
    session.send("My name is Ada")
    reply = session.send("What is my name?")
    assert reply.text == "Your name is Ada."
    assert [m["role"] for m in client.seen_messages[1]] == [
        "system",
        "user",
        "assistant",
        "user",
    ]


def test_history_trimming_preserves_system_and_newest_pair():
    client = MockClient()
    session = make_session(client, max_pairs=1)
    session.send("first")
    session.send("second")
    assert client.seen_messages[-1][0]["role"] == "system"
    assert all(message["content"] != "first" for message in client.seen_messages[-1])
    assert session.trimmed_pairs == 1


def test_cost_calculation():
    assert estimate_cost(Usage(1_000_000, 500_000), 0.40, 1.60) == pytest.approx(1.20)


@pytest.mark.parametrize(
    ("failure", "error_type"),
    [
        ("auth", AuthenticationFailure),
        ("rate", RateLimitFailure),
        ("network", NetworkFailure),
    ],
)
def test_expected_errors_are_classified(failure, error_type):
    with pytest.raises(error_type):
        make_session(MockClient(failure)).send("hello")


def test_failed_turn_is_not_saved():
    session = make_session(MockClient("network"))
    with pytest.raises(NetworkFailure):
        session.send("not remembered")
    assert session.messages == [{"role": "system", "content": "You are a test tutor."}]


def test_exit_makes_no_model_call():
    client = MockClient()
    output = []
    chat_loop(make_session(client), lambda _: "exit", output.append)
    assert client.calls == 0
    assert output[-1] == "Session ended."


def test_usage_accumulates_across_turns():
    session = make_session()
    first = session.send("one")
    second = session.send("two")
    assert session.total_usage == first.usage + second.usage

