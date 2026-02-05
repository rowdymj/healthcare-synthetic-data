#!/usr/bin/env python3
"""
Validate referential integrity and basic schema sanity for the synthetic dataset.
"""

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "json"


def load(name):
    path = DATA_DIR / name
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def index_by_id(items, key):
    return {item[key] for item in items if key in item}


def main():
    employers = load("employers.json")
    plans = load("plans.json")
    benefits = load("benefits.json")
    providers = load("providers.json")
    members = load("members.json")
    dependents = load("dependents.json")
    eligibility = load("eligibility.json")
    medical_claims = load("medical_claims.json")
    claim_lines = load("claim_lines.json")
    pharmacy_claims = load("pharmacy_claims.json")
    authorizations = load("authorizations.json")
    accumulators = load("accumulators.json")
    call_logs = load("call_logs.json")
    secure_messages = load("secure_messages.json")
    case_notes = load("case_notes.json")
    agents = load("agents.json")

    employer_ids = index_by_id(employers, "employer_id")
    plan_ids = index_by_id(plans, "plan_id")
    provider_ids = index_by_id(providers, "provider_id")
    member_ids = index_by_id(members, "member_id")
    dependent_ids = index_by_id(dependents, "member_id")
    covered_ids = member_ids | dependent_ids
    subscriber_ids = {m.get("subscriber_id") for m in members if m.get("subscriber_id")}
    claim_ids = index_by_id(medical_claims, "claim_id")
    auth_ids = index_by_id(authorizations, "auth_id")
    agent_ids = index_by_id(agents, "agent_id")

    errors = []

    def require(ref_value, valid_set, context):
        if ref_value is None:
            return
        if ref_value not in valid_set:
            errors.append(f"{context}: {ref_value} not found")

    for m in members:
        require(m.get("employer_id"), employer_ids, f"members.employer_id for {m.get('member_id')}")
        require(m.get("plan_id"), plan_ids, f"members.plan_id for {m.get('member_id')}")
        require(m.get("pcp_provider_id"), provider_ids, f"members.pcp_provider_id for {m.get('member_id')}")

    for d in dependents:
        require(d.get("subscriber_member_id"), member_ids, f"dependents.subscriber_member_id for {d.get('member_id')}")
        require(d.get("employer_id"), employer_ids, f"dependents.employer_id for {d.get('member_id')}")
        require(d.get("plan_id"), plan_ids, f"dependents.plan_id for {d.get('member_id')}")
        if d.get("subscriber_id") and d.get("subscriber_id") not in subscriber_ids:
            errors.append(f"dependents.subscriber_id for {d.get('member_id')}: {d.get('subscriber_id')} not found")

    for e in eligibility:
        require(e.get("member_id"), covered_ids, f"eligibility.member_id for {e.get('eligibility_id')}")
        require(e.get("plan_id"), plan_ids, f"eligibility.plan_id for {e.get('eligibility_id')}")

    for c in medical_claims:
        require(c.get("member_id"), covered_ids, f"medical_claims.member_id for {c.get('claim_id')}")
        require(c.get("plan_id"), plan_ids, f"medical_claims.plan_id for {c.get('claim_id')}")
        require(c.get("provider_id"), provider_ids, f"medical_claims.provider_id for {c.get('claim_id')}")

    for cl in claim_lines:
        require(cl.get("claim_id"), claim_ids, f"claim_lines.claim_id for {cl.get('claim_line_id')}")

    for rx in pharmacy_claims:
        require(rx.get("member_id"), covered_ids, f"pharmacy_claims.member_id for {rx.get('rx_claim_id')}")
        require(rx.get("plan_id"), plan_ids, f"pharmacy_claims.plan_id for {rx.get('rx_claim_id')}")

    for a in authorizations:
        require(a.get("member_id"), covered_ids, f"authorizations.member_id for {a.get('auth_id')}")
        require(a.get("plan_id"), plan_ids, f"authorizations.plan_id for {a.get('auth_id')}")
        require(a.get("provider_id"), provider_ids, f"authorizations.provider_id for {a.get('auth_id')}")

    for acc in accumulators:
        require(acc.get("member_id"), covered_ids, f"accumulators.member_id for {acc.get('accumulator_id')}")
        require(acc.get("plan_id"), plan_ids, f"accumulators.plan_id for {acc.get('accumulator_id')}")

    for call in call_logs:
        require(call.get("member_id"), covered_ids, f"call_logs.member_id for {call.get('call_id')}")
        require(call.get("agent_id"), agent_ids, f"call_logs.agent_id for {call.get('call_id')}")
        if call.get("related_claim_id"):
            require(call.get("related_claim_id"), claim_ids, f"call_logs.related_claim_id for {call.get('call_id')}")
        if call.get("related_auth_id"):
            require(call.get("related_auth_id"), auth_ids, f"call_logs.related_auth_id for {call.get('call_id')}")

    for msg in secure_messages:
        require(msg.get("member_id"), covered_ids, f"secure_messages.member_id for {msg.get('message_id')}")
        if msg.get("related_claim_id"):
            require(msg.get("related_claim_id"), claim_ids, f"secure_messages.related_claim_id for {msg.get('message_id')}")

    for note in case_notes:
        require(note.get("member_id"), covered_ids, f"case_notes.member_id for {note.get('note_id')}")
        if note.get("related_claim_id"):
            require(note.get("related_claim_id"), claim_ids, f"case_notes.related_claim_id for {note.get('note_id')}")
        if note.get("related_auth_id"):
            require(note.get("related_auth_id"), auth_ids, f"case_notes.related_auth_id for {note.get('note_id')}")

    if errors:
        print("Data validation failed:")
        for err in errors[:50]:
            print(f"- {err}")
        if len(errors) > 50:
            print(f"... {len(errors) - 50} more")
        sys.exit(1)

    print("Data validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
