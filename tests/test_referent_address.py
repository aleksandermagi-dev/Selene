from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_spine import build_conversation_spine
from selene.db import connect, init_db
from selene.dialogue_workspace import prepare_dialogue_turn
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.referent_address import referent_address_status, resolve_referent_address


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
        ("Referent and address test", "selene_chat_active", "selene_native_speech"),
    )
    conn.commit()
    session_id = int(
        conn.execute(
            "SELECT id FROM selene_chat_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
    )
    return conn, session_id


def test_identity_independent_naming_law_is_inspectable():
    status = referent_address_status()

    assert status["status"] == "referent_address_resolver_ready"
    assert status["law"]["same_individual_may_have_multiple_names"] is True
    assert status["law"]["same_name_may_refer_to_multiple_individuals"] is True
    assert status["law"]["reference_correction_is_identity_correction"] is False
    assert status["persistent_alias_write_allowed"] is False
    assert status["guards"]["identity_change"] is False


def test_direct_endearment_resolves_to_current_addressee_without_retention(tmp_path):
    conn, session_id = _conn(tmp_path)

    result = resolve_referent_address(
        conn,
        {
            "session_id": session_id,
            "text": "Hey babe, what do you think?",
            "speaker_context": {"speaker": "Aleks", "source": "explicit_test_actor"},
        },
    )

    assert result["direct_address"]["token"].lower() == "babe"
    assert result["direct_address"]["address_class"] == "term_of_endearment"
    assert result["direct_address"]["referent"] == "Selene"
    assert result["direct_address"]["must_be_echoed_in_reply"] is False
    assert result["persistent_alias_written"] is False
    assert result["memory_proposal_created"] is False
    assert result["relationship_inferred"] is False


def test_baby_literal_figurative_and_quoted_uses_are_not_direct_address(tmp_path):
    conn, session_id = _conn(tmp_path)
    examples = {
        "The baby is sleeping.": "literal_or_generic_reference",
        "This project is my baby.": "figurative_object_reference",
        'She called him "baby" in the story.': "quoted_use",
    }

    for text, expected_use in examples.items():
        result = resolve_referent_address(
            conn,
            {"session_id": session_id, "text": text},
        )
        assert result["direct_address"] is None
        baby = next(
            item for item in result["mentions"] if item["token"].lower() == "baby"
        )
        assert baby["use"] == expected_use
        assert baby["identity_claim"] is False


def test_ordinary_love_and_honey_words_do_not_become_relationship_claims(tmp_path):
    conn, session_id = _conn(tmp_path)

    love = resolve_referent_address(
        conn,
        {"session_id": session_id, "text": "I love how this design fits together."},
    )
    honey = resolve_referent_address(
        conn,
        {"session_id": session_id, "text": "Honey tastes different in each recipe."},
    )

    assert love["direct_address"] is None
    assert love["ask_if_materially_ambiguous"] is False
    assert next(item for item in love["mentions"] if item["token"].lower() == "love")[
        "use"
    ] == "literal_or_generic_reference"
    assert honey["direct_address"] is None
    assert honey["relationship_inferred"] is False


def test_multiple_names_can_point_to_one_session_referent(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Aleksander, Aleks, Magi, and Alec all refer to me."

    result = resolve_referent_address(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "speaker_context": {"speaker": "Aleks", "source": "explicit_test_actor"},
        },
    )

    assertion = result["alias_assertions"][0]
    assert assertion["referent"] == "Aleks"
    assert assertion["aliases"] == ["Aleksander", "Aleks", "Magi", "Alec"]
    assert assertion["creates_additional_individuals"] is False
    assert assertion["durable_write"] is False
    assert result["identity_continuity_affected"] is False


def test_address_preferences_are_session_scoped_and_can_be_revised(tmp_path):
    conn, session_id = _conn(tmp_path)
    first = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Call me Aleks for now.",
            "speaker_context": {"speaker": "current_user", "source": "chat_channel"},
            "intent_decision": classify_chat_intent("Call me Aleks for now."),
        },
    )
    second = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Don't call me Alec.",
            "speaker_context": {"speaker": "current_user", "source": "chat_channel"},
            "intent_decision": classify_chat_intent("Don't call me Alec."),
        },
    )

    first_resolution = first["pragmatics"]["referent_address"]
    second_resolution = second["pragmatics"]["referent_address"]
    assert first_resolution["address_preferences"]["current_user"]["preferred"] == [
        "Aleks"
    ]
    assert second_resolution["address_preferences"]["current_user"]["preferred"] == [
        "Aleks"
    ]
    assert second_resolution["address_preferences"]["current_user"]["avoid"] == [
        "Alec"
    ]
    assert second_resolution["persistent_alias_written"] is False


def test_reference_correction_changes_reference_not_identity(tmp_path):
    conn, session_id = _conn(tmp_path)

    result = resolve_referent_address(
        conn,
        {"session_id": session_id, "text": "I meant Ranger, not Aleks."},
    )

    assert result["referent_corrections"] == [
        {
            "replacement": "Ranger",
            "replaced": "Aleks",
            "scope": "current_session_reference_only",
            "identity_change": False,
            "durable_write": False,
        }
    ]
    assert result["corrections_update_reference_not_identity"] is True


def test_reviewed_nickname_note_informs_a_mention_without_assigning_identity(tmp_path):
    conn, session_id = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO continuity_notes
        (note_type, label, aliases, meaning, allowed_use, prohibited_use,
         status, confidence, source, source_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "nickname",
            "Starfire",
            "Aleks|Aleksander",
            "A reviewed layered callsign.",
            "Use only when context supports it.",
            "Do not flatten or force it.",
            "usable_reviewed_evidence",
            "strong",
            "test_review",
            "test:starfire",
        ),
    )
    conn.commit()

    result = resolve_referent_address(
        conn,
        {"session_id": session_id, "text": "What does Starfire mean here?"},
    )

    mention = next(item for item in result["mentions"] if item["token"] == "Starfire")
    assert mention["use"] == "reviewed_nickname_mention"
    assert mention["resolved_to"] == ""
    assert mention["identity_claim"] is False
    assert result["reviewed_nickname_note_ids_considered"]


def test_material_person_ambiguity_asks_once_without_guessing(tmp_path):
    conn, session_id = _conn(tmp_path)

    result = resolve_referent_address(
        conn,
        {"session_id": session_id, "text": "What did baby tell honey?"},
    )

    assert result["direct_address"] is None
    assert result["ambiguity"]["material"] is True
    assert result["ask_if_materially_ambiguous"] is True
    assert result["ambiguity"]["question"] == "Which person are you referring to?"


def test_dialogue_spine_and_nlo_receive_address_without_forcing_echo(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Hey sweetie, can we compare the two plans?"
    dialogue = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
        },
    )
    spine = build_conversation_spine(
        {
            "session_id": session_id,
            "prompt": text,
            "dialogue_workspace": dialogue,
            "intent_decision": classify_chat_intent(text),
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": text,
            "content_seed": "We can compare their cost and reliability.",
            "dialogue_workspace": dialogue,
            "conversation_spine": spine,
            "intent_decision": classify_chat_intent(text),
        },
    )

    assert (
        dialogue["pragmatics"]["referent_address"]["direct_address"]["referent"]
        == "Selene"
    )
    assert spine["referent_address"]["direct_address"]["token"].lower() == "sweetie"
    assert nlo["meaning_packet"]["referent_address"]["direct_address"]["token"].lower() == "sweetie"
    assert nlo["meaning_packet"]["address_term_must_be_echoed"] is False


def test_router_exposes_status_and_resolution(tmp_path):
    conn, session_id = _conn(tmp_path)

    status = route_request(conn, "referent_address.status")["result"]
    resolution = route_request(
        conn,
        "referent_address.resolve",
        {"session_id": session_id, "text": "Selene, I have an idea."},
    )["result"]

    assert status["status"] == "referent_address_resolver_ready"
    assert resolution["direct_address"]["referent"] == "Selene"
    assert resolution["guards"]["memory_write_active"] is False
