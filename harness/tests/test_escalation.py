"""Tests for harness.escalation — mandatory and soft escalation triggers."""

from harness.escalation import EscalationEngine, EscalationConfig


def _engine(config=None):
    return EscalationEngine(config or EscalationConfig())


def _clean_result(**overrides):
    base = {
        "is_adverse_determination": False,
        "is_high_dollar": False,
        "claim_amount": 500.0,
        "is_appeal_decision": False,
        "is_clinical_complexity": False,
        "confidence": 0.95,
        "missing_data_fraction": 0.05,
    }
    base.update(overrides)
    return base


def test_adverse_determination_mandatory_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result(is_adverse_determination=True))
    assert result.should_escalate is True
    assert result.mandatory is True
    assert "adverse determination" in result.reason


def test_appeal_decision_mandatory_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result(is_appeal_decision=True))
    assert result.should_escalate is True
    assert result.mandatory is True
    assert "appeal decision" in result.reason


def test_high_dollar_mandatory_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result(claim_amount=47000.0, is_high_dollar=True))
    assert result.should_escalate is True
    assert result.mandatory is True
    assert "high dollar" in result.reason


def test_low_confidence_soft_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result(confidence=0.6))
    assert result.should_escalate is True
    assert result.mandatory is False
    assert "confidence" in result.reason.lower()


def test_high_missing_data_soft_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result(missing_data_fraction=0.5))
    assert result.should_escalate is True
    assert result.mandatory is False
    assert "missing data" in result.reason.lower()


def test_clean_case_no_escalation():
    engine = _engine()
    result = engine.evaluate(_clean_result())
    assert result.should_escalate is False
    assert result.mandatory is False


def test_mandatory_cannot_be_overridden_by_high_confidence():
    """Mandatory trigger fires even with confidence=1.0."""
    engine = _engine()
    result = engine.evaluate(
        _clean_result(is_adverse_determination=True, confidence=1.0)
    )
    assert result.should_escalate is True
    assert result.mandatory is True
