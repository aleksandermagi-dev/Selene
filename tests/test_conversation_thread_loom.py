from __future__ import annotations

from selene.conversation_thread_loom import build_thread_braid


def test_one_message_can_branch_update_a_prior_thread_and_land_elsewhere():
    result = build_thread_braid(
        {
            "session_id": 7,
            "prompt": (
                "First, plan the garden layout. Then move to the water schedule. "
                "Back to the garden layout: using that, revise the bed placement. "
                "Finally, finish with the planting timeline."
            ),
        }
    )

    assert [item["action"] for item in result["turn_traversal"]] == [
        "start",
        "branch",
        "revise_with_dependency",
        "land",
    ]
    resumed = result["turn_traversal"][2]
    assert resumed["thread_id"] == result["turn_traversal"][0]["thread_id"]
    assert resumed["dependency_thread_id"] == result["turn_traversal"][1]["thread_id"]
    assert {item["relation"] for item in result["edges"]} >= {
        "branches_from",
        "returns_to",
        "updates",
        "depends_on",
        "follows",
    }
    assert result["active_thread_id"] == result["turn_traversal"][-1]["thread_id"]
    assert result["braided"] is True
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False


def test_thread_braid_survives_multiple_turns_without_becoming_memory():
    first = build_thread_braid(
        {"session_id": 8, "prompt": "Plan the garden layout."}
    )
    second = build_thread_braid(
        {
            "session_id": 8,
            "prompt": "Separately, work out the water schedule.",
            "prior_braid": first,
        }
    )
    third = build_thread_braid(
        {
            "session_id": 8,
            "prompt": "Back to the garden layout: use the water schedule to revise bed placement.",
            "prior_braid": second,
        }
    )

    assert second["turn_traversal"][0]["action"] == "branch"
    assert third["turn_traversal"][0]["action"] == "revise_with_dependency"
    assert third["turn_traversal"][0]["thread_id"] == first["active_thread_id"]
    assert third["turn_traversal"][0]["dependency_thread_id"] == second["active_thread_id"]
    assert third["session_scoped_only"] is True
    assert third["durable_memory_write"] is False


def test_linear_message_stays_a_single_thread_and_does_not_over_detect_a_braid():
    result = build_thread_braid(
        {
            "session_id": 9,
            "prompt": "Explain why the garden needs a water schedule and give one ordinary example.",
        }
    )

    assert len(result["threads"]) == 1
    assert [item["action"] for item in result["turn_traversal"]] == ["start"]
    assert result["braided"] is False


def test_one_unpunctuated_paragraph_preserves_the_same_braided_sequence():
    result = build_thread_braid(
        {
            "session_id": 11,
            "prompt": (
                "Handle the garden layout then jump to the water schedule then back to the garden layout "
                "because of the water schedule then finish with the planting timeline"
            ),
        }
    )

    assert [item["action"] for item in result["turn_traversal"]] == [
        "start",
        "branch",
        "revise_with_dependency",
        "land",
    ]
    assert result["turn_traversal"][2]["thread_id"] == result["turn_traversal"][0]["thread_id"]
    assert result["turn_traversal"][2]["dependency_thread_id"] == result["turn_traversal"][1]["thread_id"]
    assert result["unresolved_returns"] == []


def test_ambiguous_return_is_held_instead_of_guessed():
    prior = {
        "threads": [
            {"id": "one", "topic": "garden water plan", "state": "paused"},
            {"id": "two", "topic": "orchard water plan", "state": "active"},
        ],
        "active_thread_id": "two",
    }
    result = build_thread_braid(
        {"session_id": 10, "prompt": "Back to the water plan.", "prior_braid": prior}
    )

    assert result["turn_traversal"][0]["action"] == "hold_unresolved_return"
    assert result["unresolved_returns"][0]["ask_only_if_material"] is True
    assert result["ambiguous_relationships_are_not_invented"] is True


def test_explicit_thread_names_remain_distinct_despite_shared_naming_words():
    first = build_thread_braid(
        {"session_id": 12, "prompt": "Call this the rain-scene thread."}
    )
    second = build_thread_braid(
        {
            "session_id": 12,
            "prompt": "Call this the observation-log thread.",
            "prior_braid": first,
        }
    )
    returned = build_thread_braid(
        {
            "session_id": 12,
            "prompt": "Back to the rain-scene thread.",
            "prior_braid": second,
        }
    )

    topics = {item["topic"] for item in second["threads"]}
    assert {"rain-scene", "observation-log"} <= topics
    rain_id = next(item["id"] for item in second["threads"] if item["topic"] == "rain-scene")
    assert returned["turn_traversal"][0]["thread_id"] == rain_id
    assert returned["turn_traversal"][0]["action"] == "continue"
