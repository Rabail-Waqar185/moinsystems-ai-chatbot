from app.chat.lead_capture import LeadState, maybe_start_lead_capture, process_turn
from app.db.models import ChatSession


def make_session(lead_state: str = LeadState.NOT_ACTIVE, lead_draft: dict | None = None) -> ChatSession:
    """In-memory ChatSession, never added to a DB session — pure object for
    testing state transitions without needing Postgres."""
    session = ChatSession()
    session.lead_state = lead_state
    session.lead_draft = lead_draft
    return session


class TestMaybeStartLeadCapture:
    def test_starts_on_pricing_intent_when_not_active(self):
        session = make_session()
        maybe_start_lead_capture(session, "pricing_quote", {"pricing_quote", "buying_intent"})
        assert session.lead_state == LeadState.COLLECTING_NAME

    def test_does_not_start_on_general_query(self):
        session = make_session()
        maybe_start_lead_capture(session, "general_query", {"pricing_quote", "buying_intent"})
        assert session.lead_state == LeadState.NOT_ACTIVE

    def test_does_not_restart_an_already_active_capture(self):
        session = make_session(lead_state=LeadState.COLLECTING_EMAIL)
        maybe_start_lead_capture(session, "pricing_quote", {"pricing_quote", "buying_intent"})
        # Must stay at collecting_email, not reset back to collecting_name.
        assert session.lead_state == LeadState.COLLECTING_EMAIL

    def test_does_not_restart_a_completed_session(self):
        session = make_session(lead_state=LeadState.COMPLETE)
        maybe_start_lead_capture(session, "pricing_quote", {"pricing_quote", "buying_intent"})
        assert session.lead_state == LeadState.COMPLETE


class TestProcessTurnNameStep:
    def test_valid_name_advances_to_email_and_saves_draft(self):
        session = make_session(lead_state=LeadState.COLLECTING_NAME)
        result = process_turn(session, "Rabail Waqar")
        assert result.completed is False
        assert result.validation_error is None
        assert session.lead_state == LeadState.COLLECTING_EMAIL
        assert session.lead_draft["full_name"] == "Rabail Waqar"

    def test_invalid_name_stays_on_same_step_with_error(self):
        session = make_session(lead_state=LeadState.COLLECTING_NAME)
        result = process_turn(session, "1")
        assert result.validation_error is not None
        assert session.lead_state == LeadState.COLLECTING_NAME

    def test_a_question_does_not_get_consumed_as_a_name(self):
        session = make_session(lead_state=LeadState.COLLECTING_NAME)
        result = process_turn(session, "What technologies do you use?")
        assert result.consumed is False
        assert session.lead_state == LeadState.COLLECTING_NAME


class TestProcessTurnEmailStep:
    def test_valid_email_advances_to_phone(self):
        session = make_session(lead_state=LeadState.COLLECTING_EMAIL, lead_draft={"full_name": "Rabail"})
        result = process_turn(session, "rabail@example.com")
        assert result.completed is False
        assert session.lead_state == LeadState.COLLECTING_PHONE
        assert session.lead_draft["email"] == "rabail@example.com"
        # Prior field must still be preserved, not overwritten.
        assert session.lead_draft["full_name"] == "Rabail"

    def test_invalid_email_stays_on_same_step(self):
        session = make_session(lead_state=LeadState.COLLECTING_EMAIL, lead_draft={"full_name": "Rabail"})
        result = process_turn(session, "not-an-email")
        assert result.validation_error is not None
        assert session.lead_state == LeadState.COLLECTING_EMAIL


class TestProcessTurnPhoneStep:
    def test_valid_phone_completes_capture(self):
        session = make_session(
            lead_state=LeadState.COLLECTING_PHONE,
            lead_draft={"full_name": "Rabail", "email": "rabail@example.com"},
        )
        result = process_turn(session, "+92 300 1234567")
        assert result.completed is True
        assert session.lead_state == LeadState.COMPLETE
        assert session.lead_draft["contact_number"] == "+92 300 1234567"

    def test_invalid_phone_does_not_complete(self):
        session = make_session(
            lead_state=LeadState.COLLECTING_PHONE,
            lead_draft={"full_name": "Rabail", "email": "rabail@example.com"},
        )
        result = process_turn(session, "123")
        assert result.completed is False
        assert session.lead_state == LeadState.COLLECTING_PHONE


class TestProcessTurnInactiveStates:
    def test_not_active_session_is_never_consumed(self):
        session = make_session(lead_state=LeadState.NOT_ACTIVE)
        result = process_turn(session, "Rabail Waqar")
        assert result.consumed is False
        assert session.lead_state == LeadState.NOT_ACTIVE

    def test_complete_session_is_never_consumed_again(self):
        session = make_session(lead_state=LeadState.COMPLETE, lead_draft={"full_name": "Rabail"})
        result = process_turn(session, "Some new message")
        assert result.consumed is False
        assert session.lead_state == LeadState.COMPLETE