#!/usr/bin/env python3
"""
Generate docs/DATA-SPECIFICATION.md from the actual JSON files in data/json.
"""

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "json"
OUT_PATH = BASE_DIR / "docs" / "DATA-SPECIFICATION.md"


ENTITIES = [
    ("Employers", "employers.json"),
    ("Plans", "plans.json"),
    ("Benefits", "benefits.json"),
    ("Providers", "providers.json"),
    ("Members", "members.json"),
    ("Dependents", "dependents.json"),
    ("Eligibility", "eligibility.json"),
    ("Medical Claims", "medical_claims.json"),
    ("Claim Lines", "claim_lines.json"),
    ("Pharmacy Claims", "pharmacy_claims.json"),
    ("Authorizations", "authorizations.json"),
    ("Accumulators", "accumulators.json"),
    ("Call Logs", "call_logs.json"),
    ("Secure Messages", "secure_messages.json"),
    ("Case Notes", "case_notes.json"),
    ("Agents", "agents.json"),
    ("Reference Diagnosis Codes", "reference_diagnosis_codes.json"),
    ("Reference Procedure Codes", "reference_procedure_codes.json"),
    ("Reference Place Of Service", "reference_place_of_service.json"),
    ("Reference Medications", "reference_medications.json"),
]


def load(path: Path):
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def type_of(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "array"
        elem_type = None
        for v in value:
            if v is None:
                continue
            elem_type = type_of(v)
            break
        return f"array[{elem_type or 'unknown'}]"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def merge_types(types):
    tset = set(types)
    if "integer" in tset and "number" in tset:
        tset.discard("integer")
        tset.add("number")
    return " | ".join(sorted(tset))


def main():
    summary = load(DATA_DIR / "summary.json") if (DATA_DIR / "summary.json").exists() else None

    lines = []
    lines.append("# Healthcare Synthetic Dataset - Data Specification")
    lines.append("")
    lines.append("**Version:** 1.1 (data-derived)")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("**Source:** `data/json/*.json`")
    lines.append("")
    lines.append("This specification is generated from the actual JSON data files. Field names and types reflect the dataset in this repo.")
    lines.append("")

    if summary:
        lines.append("## Summary")
        lines.append("")
        counts = summary.get("entity_counts", {})
        financials = summary.get("financial_summary", {})
        if counts:
            lines.append("**Entity Counts**")
            lines.append("")
            for key, value in counts.items():
                lines.append(f"- {key.replace('_',' ').title()}: {value}")
            lines.append("")
        if financials:
            lines.append("**Financial Summary**")
            lines.append("")
            for key, value in financials.items():
                lines.append(f"- {key.replace('_',' ').title()}: {value}")
            lines.append("")

    lines.append("## Entities")
    lines.append("")

    for label, filename in ENTITIES:
        path = DATA_DIR / filename
        if not path.exists():
            continue
        data = load(path)
        count = len(data)

        type_map = {}
        example_map = {}
        for i, row in enumerate(data):
            if i == 0:
                for k, v in row.items():
                    example_map[k] = v
            for k, v in row.items():
                type_map.setdefault(k, set()).add(type_of(v))

        lines.append(f"### {label} ({count})")
        lines.append("")
        lines.append("| Field | Type(s) | Example |")
        lines.append("|-------|---------|---------|")
        for field in sorted(type_map.keys()):
            types = merge_types(type_map[field]).replace("|", "\\|")
            example = example_map.get(field)
            example_str = json.dumps(example, ensure_ascii=True)
            lines.append(f"| {field} | `{types}` | `{example_str}` |")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
