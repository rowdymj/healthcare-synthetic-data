"""
Healthcare Insurance Member Interaction History Generator

Generates realistic interaction data including call logs, secure messages,
case notes, and agent profiles for a healthcare synthetic dataset.
"""

import json
import csv
import random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import uuid

# Set random seed for reproducibility
random.seed(42)

# Configuration (repo-relative)
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
JSON_DIR = DATA_DIR / "json"
CSV_DIR = DATA_DIR / "csv"
GENERATOR_DIR = Path(__file__).parent

# Constants
CALL_REASONS = [
    "Claim Status Inquiry",
    "Benefits Question",
    "Coverage Verification",
    "Prior Auth Status",
    "Billing Dispute",
    "ID Card Request",
    "PCP Change",
    "Prescription Question",
    "Appeal Request",
    "General Inquiry",
    "Complaint",
    "Enrollment Question"
]

CALL_TYPES = ["Inbound", "Outbound"]
DISPOSITIONS = ["Resolved", "Escalated", "Callback Scheduled", "Transferred", "Voicemail"]
SENTIMENTS = ["Positive", "Neutral", "Frustrated", "Angry"]

CASE_CATEGORIES = [
    "Clinical Review",
    "Billing",
    "Enrollment",
    "Grievance",
    "Appeal",
    "Care Coordination",
    "Utilization Management"
]

MESSAGE_STATUSES = ["Read", "Unread", "Replied", "Closed"]
MESSAGE_PRIORITIES = ["Normal", "High", "Urgent"]

DEPARTMENTS = ["Member Services", "Claims", "Clinical", "Pharmacy", "Enrollment", "Appeals"]
ROLES = ["Agent", "Senior Agent", "Supervisor", "Clinical Reviewer"]

FIRST_NAMES = [
    "Sarah", "Michael", "Jennifer", "David", "Lisa", "James", "Maria", "Robert",
    "Patricia", "John", "Christopher", "Karen", "Daniel", "Nancy", "Matthew",
    "Sandra", "Anthony", "Ashley", "Mark", "Katherine"
]

LAST_NAMES = [
    "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"
]

MEDICATIONS_BY_TIER = {
    "Tier 1 Generic": ["Lisinopril 10mg", "Metformin 500mg", "Atorvastatin 20mg"],
    "Tier 2 Preferred Brand": ["Januvia 100mg", "Advair Diskus", "Crestor 10mg"],
    "Tier 3 Non-Preferred Brand": ["Lyrica 75mg", "Humira Pen", "Xeljanz 5mg"],
    "Tier 4 Specialty": ["Ozempic 1mg", "Dupixent Pen", "Rinvoq 5mg"]
}

# Sample medical procedures and diagnoses
PROCEDURES = [
    "knee replacement",
    "hip replacement",
    "cataract surgery",
    "colonoscopy",
    "MRI scan",
    "CT scan",
    "X-ray",
    "ultrasound",
    "echocardiogram",
    "cardiac catheterization",
    "lumbar spine surgery",
    "ACL reconstruction"
]

DIAGNOSES = [
    "Type 2 diabetes",
    "hypertension",
    "osteoarthritis",
    "depression",
    "anxiety disorder",
    "COPD",
    "asthma",
    "heart disease",
    "chronic back pain",
    "migraine headaches"
]


def load_existing_data() -> Dict[str, Any]:
    """Load existing data from JSON files and build member-to-claims indexes."""
    data = {}

    print("Loading existing data...")

    # Load members
    with open(JSON_DIR / "members.json", "r") as f:
        data["members"] = json.load(f)
    print(f"Loaded {len(data['members'])} members")

    # Load medical claims
    with open(JSON_DIR / "medical_claims.json", "r") as f:
        data["medical_claims"] = json.load(f)
    print(f"Loaded {len(data['medical_claims'])} medical claims")

    # Load pharmacy claims
    with open(JSON_DIR / "pharmacy_claims.json", "r") as f:
        data["pharmacy_claims"] = json.load(f)
    print(f"Loaded {len(data['pharmacy_claims'])} pharmacy claims")

    # Load authorizations
    with open(JSON_DIR / "authorizations.json", "r") as f:
        data["authorizations"] = json.load(f)
    print(f"Loaded {len(data['authorizations'])} authorizations")

    # Build member -> claim_ids and member -> auth_ids indexes
    claims_by_member = defaultdict(list)
    for c in data["medical_claims"]:
        claims_by_member[c["member_id"]].append(c["claim_id"])
    data["claims_by_member"] = claims_by_member

    auths_by_member = defaultdict(list)
    for a in data["authorizations"]:
        auths_by_member[a["member_id"]].append(a["auth_id"])
    data["auths_by_member"] = auths_by_member

    return data


def generate_call_id() -> str:
    """Generate a unique call ID"""
    return f"CALL-{uuid.uuid4().hex[:8].upper()}"


def generate_message_id() -> str:
    """Generate a unique message ID"""
    return f"MSG-{uuid.uuid4().hex[:8].upper()}"


def generate_thread_id() -> str:
    """Generate a unique thread ID"""
    return f"THD-{uuid.uuid4().hex[:8].upper()}"


def generate_note_id() -> str:
    """Generate a unique note ID"""
    return f"NOTE-{uuid.uuid4().hex[:8].upper()}"


def generate_case_id() -> str:
    """Generate a unique case ID"""
    return f"CASE-{uuid.uuid4().hex[:8].upper()}"


def generate_agent_id() -> str:
    """Generate a unique agent ID"""
    return f"AGT-{uuid.uuid4().hex[:8].upper()}"


def generate_agent_name() -> str:
    """Generate a random agent name"""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_random_date(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random date between start and end dates"""
    time_between = (end_date - start_date).days
    random_days = random.randint(0, time_between)
    return start_date + timedelta(days=random_days)


def generate_call_logs(data: Dict, count: int = 3000) -> List[Dict[str, Any]]:
    """Generate realistic call logs with same-member claim/auth references."""
    print(f"\nGenerating {count} call logs...")

    call_logs = []
    member_ids = [m["member_id"] for m in data["members"]]
    claim_ids = [c["claim_id"] for c in data["medical_claims"]]
    claims_by_member = data["claims_by_member"]
    auths_by_member = data["auths_by_member"]

    agent_ids = [f"AGT-{i:04d}" for i in range(1, 21)]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 2, 28)

    for _ in range(count):
        call_date = generate_random_date(start_date, end_date)
        call_time = f"{random.randint(8, 17):02d}:{random.randint(0, 59):02d}:00"
        duration = random.choice(
            list(range(60, 180, 30)) +  # Short calls
            list(range(180, 600, 60)) +  # Medium calls
            list(range(600, 1800, 120))   # Longer calls
        )

        call_reason = random.choice(CALL_REASONS)
        sentiment = random.choices(
            SENTIMENTS,
            weights=[40, 35, 15, 10]  # Most calls neutral/positive
        )[0]

        # Generate realistic notes based on call reason
        notes = generate_call_note(call_reason, member_ids, claim_ids)

        disposition = random.choices(
            DISPOSITIONS,
            weights=[60, 15, 15, 5, 5]
        )[0]

        member_id = random.choice(member_ids)
        member_claims = claims_by_member.get(member_id, [])
        member_auths = auths_by_member.get(member_id, [])

        call_log = {
            "call_id": generate_call_id(),
            "member_id": member_id,
            "agent_id": random.choice(agent_ids),
            "call_date": call_date.strftime("%Y-%m-%d"),
            "call_time": call_time,
            "duration_seconds": duration,
            "call_type": random.choice(CALL_TYPES),
            "call_reason": call_reason,
            "disposition": disposition,
            "related_claim_id": random.choice(member_claims) if member_claims and random.random() > 0.5 else None,
            "related_auth_id": random.choice(member_auths) if member_auths and random.random() > 0.5 else None,
            "sentiment": sentiment,
            "notes": notes,
            "queue_wait_seconds": random.randint(0, 900),
            "first_call_resolution": random.choice([True, False]) if disposition == "Resolved" else False,
            "ivr_path": generate_ivr_path()
        }

        call_logs.append(call_log)

    return call_logs


def generate_call_note(call_reason: str, member_ids: List[str], claim_ids: List[str]) -> str:
    """Generate realistic call notes based on the call reason"""

    notes_templates = {
        "Claim Status Inquiry": [
            f"Member called regarding claim {random.choice(claim_ids[:10])}. Provided claim status and expected payment date.",
            "Member inquiring about submitted claim. Explained processing timeline and provided claim reference number.",
            "Called to check on claim status. Located claim and advised it's currently under review."
        ],
        "Benefits Question": [
            "Member asking about deductible status and remaining benefits. Pulled EOB and reviewed covered services.",
            "Verified coverage details for member's plan. Explained copay structure and out-of-pocket maximum.",
            "Member had questions about preventive care coverage. Confirmed annual physical and screening tests are covered at no cost."
        ],
        "Coverage Verification": [
            "Pre-service verification completed. Confirmed member has active coverage and in-network status for requested service.",
            "Member requested verification for upcoming procedure. Confirmed $2,500 deductible remaining and surgery benefits.",
            "Verified coverage for specialist visit. Confirmed referral not needed and member has $500 copay."
        ],
        "Prior Auth Status": [
            f"Member following up on prior authorization request {random.choice(claim_ids[:5])}. Auth is pending clinical review.",
            "Checked authorization status for specialist referral. Auth approved for 4 visits within 90 days.",
            "Member called regarding delayed auth. Escalated to clinical team for expedited review."
        ],
        "Billing Dispute": [
            "Member received unexpected bill. Reviewed claim and identified it was processed in-network. Correcting bill and crediting account.",
            "Disputed charge on EOB. Located duplicate billing and working with provider to correct and refund.",
            "Member questioning provider balance bill. Explained network status and encouraged provider contact."
        ],
        "ID Card Request": [
            "Member reported lost ID card. Expedited replacement card mailed same day. Provided digital card via secure message.",
            "Requested replacement ID card due to damaged card. Processed replacement and provided group/member numbers.",
            "New dependent added to account. Requested ID cards for entire family. Mailed same day."
        ],
        "PCP Change": [
            "Member requested to change primary care physician. Processed change effective immediately. Sent confirmation and new PCP information.",
            "Updated PCP selection to new provider within network. Changes effective immediately.",
            "Member switching PCP due to relocation. Updated systems and sent new PCP welcome packet."
        ],
        "Prescription Question": [
            "Member inquiring about medication formulary status. Advised Tier 3 non-preferred with $150 copay. Discussed generic alternative.",
            "Member asking about specialty medication coverage. Reviewed prior authorization requirement and referred to pharmacy for details.",
            "Called regarding high copay for prescribed medication. Reviewed formulary tier and provided patient assistance program information."
        ],
        "Appeal Request": [
            "Member requested appeal of denied claim. Initiated formal appeal process and mailed appeal form.",
            "Member filing appeal for non-covered service. Explained appeal timeline and provided documentation requirements.",
            "Initiated urgent appeal for time-sensitive claim denial. Fast-tracked to clinical review team."
        ],
        "General Inquiry": [
            "Member called with general plan questions. Provided policy information and directed to resources available on member portal.",
            "General information request about plan benefits. Reviewed coverage details and sent supporting documentation.",
            "Member asking about account status. Confirmed no issues and provided account summary."
        ],
        "Complaint": [
            "Member filed complaint regarding billing error. Documented complaint, corrected issue, and issued refund.",
            "Complaint received about prior experience with claims processing. Reviewed account history and apologized for delay.",
            "Member complaining about network provider experience. Documented complaint and forwarded to quality assurance team."
        ],
        "Enrollment Question": [
            "New member enrollment question answered. Confirmed coverage effective date and explained benefits.",
            "Member asking about plan changes for upcoming year. Reviewed options and sent plan comparison.",
            "Dependent enrollment request. Processed addition and mailed confirmation and ID cards."
        ]
    }

    return random.choice(notes_templates.get(call_reason, ["Member inquiry processed."]))


def generate_ivr_path() -> str:
    """Generate realistic IVR path"""
    paths = [
        "1 > Agent",
        "2 > Agent",
        "1 > 3 > Agent",
        "2 > 1 > Agent",
        "3 > 2 > Agent",
        "1 > 2 > 3 > Agent",
        "Voicemail"
    ]
    return random.choice(paths)


def generate_secure_messages(data: Dict, count: int = 2000) -> List[Dict[str, Any]]:
    """Generate realistic secure messages with same-member claim references."""
    print(f"Generating {count} secure messages...")

    messages = []
    member_ids = [m["member_id"] for m in data["members"]]
    claim_ids = [c["claim_id"] for c in data["medical_claims"]]
    claims_by_member = data["claims_by_member"]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 2, 28)

    message_threads = {}

    for i in range(count):
        thread_id = generate_thread_id() if random.random() > 0.7 else None
        if thread_id:
            if thread_id not in message_threads:
                message_threads[thread_id] = {
                    "messages": [],
                    "status": random.choice(MESSAGE_STATUSES)
                }

        sent_date = generate_random_date(start_date, end_date)
        category = random.choice(CALL_REASONS)
        direction = random.choice(["Inbound", "Outbound"])

        subject, body = generate_message_content(category, direction, claim_ids)

        priority = random.choices(
            MESSAGE_PRIORITIES,
            weights=[70, 20, 10]
        )[0]

        status = random.choices(
            MESSAGE_STATUSES,
            weights=[40, 20, 25, 15]
        )[0]

        response_time = None
        if status == "Replied" and direction == "Outbound":
            response_time = round(random.uniform(0.5, 48), 1)

        member_id = random.choice(member_ids)
        member_claims = claims_by_member.get(member_id, [])

        message = {
            "message_id": generate_message_id(),
            "thread_id": thread_id,
            "member_id": member_id,
            "direction": direction,
            "sent_date": sent_date.strftime("%Y-%m-%d %H:%M:%S"),
            "subject": subject,
            "body": body,
            "category": category,
            "status": status,
            "related_claim_id": random.choice(member_claims) if member_claims and random.random() > 0.5 else None,
            "priority": priority,
            "response_time_hours": response_time
        }

        messages.append(message)

    return messages


def generate_message_content(category: str, direction: str, claim_ids: List[str]) -> tuple:
    """Generate realistic message subject and body"""

    subjects = {
        "Claim Status Inquiry": f"Status Update - Claim {random.choice(claim_ids[:10])[:10]}",
        "Benefits Question": "Question About Coverage Benefits",
        "Coverage Verification": "Coverage Verification Request",
        "Prior Auth Status": "Prior Authorization Status",
        "Billing Dispute": "Billing Question",
        "ID Card Request": "ID Card Replacement",
        "PCP Change": "Primary Care Physician Change Request",
        "Prescription Question": "Medication Coverage Question",
        "Appeal Request": "Claim Appeal Submission",
        "General Inquiry": "General Account Question",
        "Complaint": "Service Complaint",
        "Enrollment Question": "Enrollment Information"
    }

    bodies = {
        "Claim Status Inquiry": [
            "Can you please provide an update on the status of my claim? I haven't received payment yet and would like to know when to expect it.",
            "I'm checking on the status of my recent medical claim. I submitted it three weeks ago but haven't heard back.",
            "Could you provide details on when my claim will be processed? I need this for my records."
        ],
        "Benefits Question": [
            "I wanted to confirm what my current deductible status is and what services are covered under my plan.",
            "Can you explain the difference between my copay and coinsurance? I received conflicting information.",
            "What is covered for annual preventive care visits under my plan?"
        ],
        "Coverage Verification": [
            "I'm scheduled for a procedure next month and need to verify coverage and any out-of-pocket costs.",
            "Can you confirm whether my specialist is in-network? I want to make sure I'm covered.",
            "I need a letter verifying my coverage for an upcoming hospitalization."
        ],
        "Prior Auth Status": [
            "I submitted a prior authorization request for a surgical procedure. Can you tell me the status?",
            "My doctor is waiting for prior auth approval. How long does this typically take?",
            "The auth number is AUTH-ABC123. Can you confirm if this was approved?"
        ],
        "Billing Dispute": [
            "I received an unexpected bill that doesn't seem right. Can you review my claim for errors?",
            "Why is the provider balance bill so high? I thought I selected an in-network provider.",
            "I see duplicate charges on my EOB. Can you investigate and correct this?"
        ],
        "ID Card Request": [
            "I need a replacement ID card as mine was damaged. Can you expedite this request?",
            "I lost my insurance card and need it for an upcoming appointment. How quickly can this be sent?",
            "Can I get an electronic copy of my ID card? I have an appointment tomorrow."
        ],
        "PCP Change": [
            "I would like to change my primary care physician to Dr. Smith who is in your network.",
            "I'm relocating and need to change my PCP. Can you help me find a provider in my new area?",
            "How do I change my PCP? I'm not satisfied with my current doctor."
        ],
        "Prescription Question": [
            "What is the copay for Ozempic under my plan? I was told it's a specialty medication.",
            "Is Levitra covered under my pharmacy benefits? What tier is it?",
            "The pharmacy said my medication isn't on the formulary. What are my options?"
        ],
        "Appeal Request": [
            "I want to appeal the denial of my claim. Please send me the appeal form and instructions.",
            "My claim was denied but I believe it should be covered. How do I start the appeal process?",
            "Can I submit an expedited appeal for a time-sensitive claim?"
        ],
        "General Inquiry": [
            "I have some general questions about my account and benefits. When would be a good time to discuss?",
            "Can you provide an overview of my current coverage and any plan changes effective next year?",
            "I'm new to the plan and have several questions. Where can I find this information?"
        ],
        "Complaint": [
            "I'm frustrated with how my recent claim was handled. The process took too long and I received poor service.",
            "I want to file a complaint about my previous interaction with a customer service representative.",
            "I've had multiple issues with billing that haven't been resolved. I need escalation."
        ],
        "Enrollment Question": [
            "I'm enrolling in your plan for the next year. Can you explain the different plan options?",
            "When does my new enrollment become effective? I need to know for my employer.",
            "Can I add family members to my existing coverage?"
        ]
    }

    subject = subjects.get(category, "Account Question")
    body_options = bodies.get(category, ["I have a question about my account."])
    body = random.choice(body_options)

    return subject, body


def generate_case_notes(data: Dict, count: int = 1500) -> List[Dict[str, Any]]:
    """Generate realistic case notes with same-member claim/auth references."""
    print(f"Generating {count} case notes...")

    case_notes = []
    member_ids = [m["member_id"] for m in data["members"]]
    claims_by_member = data["claims_by_member"]
    auths_by_member = data["auths_by_member"]

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 2, 28)

    for _ in range(count):
        category = random.choice(CASE_CATEGORIES)
        created_date = generate_random_date(start_date, end_date)

        note_type = random.choices(
            ["System", "Manual", "Auto-generated"],
            weights=[30, 50, 20]
        )[0]

        content = generate_case_note_content(category)
        follow_up_required = random.choices([True, False], weights=[30, 70])[0]

        follow_up_date = None
        if follow_up_required:
            days_ahead = random.randint(1, 30)
            follow_up_date = (created_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        status = random.choices(
            ["Open", "Closed", "Pending Review"],
            weights=[25, 50, 25]
        )[0]

        member_id = random.choice(member_ids)
        member_claims = claims_by_member.get(member_id, [])
        member_auths = auths_by_member.get(member_id, [])

        case_note = {
            "note_id": generate_note_id(),
            "member_id": member_id,
            "case_id": generate_case_id(),
            "author": generate_agent_name(),
            "created_date": created_date.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "note_type": note_type,
            "content": content,
            "related_claim_id": random.choice(member_claims) if member_claims and random.random() > 0.5 else None,
            "related_auth_id": random.choice(member_auths) if member_auths and random.random() > 0.5 else None,
            "follow_up_required": follow_up_required,
            "follow_up_date": follow_up_date,
            "status": status
        }

        case_notes.append(case_note)

    return case_notes


def generate_case_note_content(category: str) -> str:
    """Generate realistic case note content"""

    templates = {
        "Clinical Review": [
            f"Completed clinical review of claim for {random.choice(PROCEDURES)}. Medical necessity confirmed. Authorization approved for 4 visits.",
            f"Peer-to-peer call conducted with provider regarding {random.choice(DIAGNOSES)} treatment plan. Discussed medical necessity of requested services.",
            "Clinical reviewer determined requested therapy is medically appropriate per evidence-based guidelines. Approved with standard utilization limits."
        ],
        "Billing": [
            "Identified billing error in provider's claim submission. Corrected coding and reprocessed. Member credit of $350 issued.",
            "Reviewed provider balance bill. Amount is non-network charge outside negotiated rate. Sent explanation to member.",
            "Coordinate of benefits applied to claim. Cross-carrier coordination determined primary payer responsibility."
        ],
        "Enrollment": [
            "Member enrolled in new plan effective 3/1/2025. Coverage summary sent via secure message. Confirmed receipt of welcome packet.",
            "Dependent added to member account. New ID cards generated and will be mailed within 5-7 business days.",
            "Plan change processed for annual enrollment period. New plan effective date set for next benefit year."
        ],
        "Grievance": [
            "Member grievance received regarding claim denial. Escalated to Appeals team for formal review within 30-day timeline.",
            "Documented formal complaint about billing practices. Member notified of appeal rights and timeframe. Case assigned for investigation.",
            "Grievance filed regarding service delay in authorization processing. Root cause identified and process improvement recommended."
        ],
        "Appeal": [
            "Formal appeal submitted for denied claim. Clinical evidence reviewed. Appeals team determined claim meets medical necessity criteria. Overturned denial.",
            "Member filed external appeal through state insurance commissioner. Documentation compiled and submitted within required timeframe.",
            "Expedited appeal processed due to time-sensitive nature of requested service. Decision made within 72 hours. Appeal approved."
        ],
        "Care Coordination": [
            f"Coordinated care plan for member with {random.choice(DIAGNOSES)}. Scheduled follow-up with primary care and specialist.",
            "Disease management referral sent to case management team. Member enrolled in chronic condition management program.",
            "Care coordinator notified of upcoming hospitalization. Discharge planning initiated to ensure continuity of care post-discharge."
        ],
        "Utilization Management": [
            "Utilization review completed for extended hospital stay. Medical necessity for additional days confirmed. Approved through day 6.",
            "Surgical pre-certification completed. Verified medical necessity and reviewed alternatives. Approved for scheduled procedure.",
            "Readmission prevention assessment completed. Care plan developed to reduce likelihood of 30-day readmission."
        ]
    }

    return random.choice(templates.get(category, ["Case note content reviewed and updated."]))


def generate_agent_profiles(count: int = 20) -> List[Dict[str, Any]]:
    """Generate agent profiles"""
    print(f"Generating {count} agent profiles...")

    agents = []
    hire_start = datetime(2015, 1, 1)
    hire_end = datetime(2024, 12, 31)

    for i in range(count):
        hire_date = generate_random_date(hire_start, hire_end)

        department = random.choice(DEPARTMENTS)

        # Assign role based on hire date (longer tenure more likely to be senior)
        tenure_years = (datetime.now() - hire_date).days / 365
        if tenure_years > 5:
            role = random.choices(ROLES, weights=[20, 50, 25, 5])[0]
        elif tenure_years > 2:
            role = random.choices(ROLES, weights=[50, 30, 15, 5])[0]
        else:
            role = random.choices(ROLES, weights=[70, 20, 8, 2])[0]

        # Satisfaction scores tend to be higher for senior roles
        base_score = 75 if role in ["Supervisor", "Senior Agent"] else 70
        satisfaction = round(random.gauss(base_score, 8), 1)
        satisfaction = max(3.0, min(5.0, satisfaction / 20))  # Scale 0-5

        # Handle time improves with tenure
        base_handle_time = 600 if role in ["Supervisor", "Clinical Reviewer"] else 480
        tenure_reduction = tenure_years * 10
        handle_time = max(300, int(base_handle_time - tenure_reduction + random.randint(-60, 60)))

        agent = {
            "agent_id": f"AGT-{i+1:04d}",
            "name": generate_agent_name(),
            "department": department,
            "role": role,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "languages": ["English"] + (["Spanish"] if random.random() > 0.7 else []),
            "avg_handle_time_seconds": handle_time,
            "satisfaction_score": round(satisfaction, 2)
        }

        agents.append(agent)

    return agents


def save_json(data: List[Dict[str, Any]], filename: str, directory: Path = JSON_DIR):
    """Save data to JSON file"""
    filepath = directory / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} records to {filepath}")


def save_csv(data: List[Dict[str, Any]], filename: str, directory: Path = CSV_DIR):
    """Save data to CSV file"""
    if not data:
        return

    filepath = directory / filename

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print(f"Saved {len(data)} records to {filepath}")


def main():
    """Main execution function"""
    print("=" * 80)
    print("Healthcare Insurance Member Interaction History Generator")
    print("=" * 80)

    # Load existing data
    data = load_existing_data()

    # Generate interaction data
    call_logs = generate_call_logs(data)
    secure_messages = generate_secure_messages(data)
    case_notes = generate_case_notes(data)
    agent_profiles = generate_agent_profiles()

    # Save to JSON
    print("\nSaving to JSON...")
    save_json(call_logs, "call_logs.json")
    save_json(secure_messages, "secure_messages.json")
    save_json(case_notes, "case_notes.json")
    save_json(agent_profiles, "agents.json")

    # Save to CSV
    print("\nSaving to CSV...")
    save_csv(call_logs, "call_logs.csv")
    save_csv(secure_messages, "secure_messages.csv")
    save_csv(case_notes, "case_notes.csv")
    save_csv(agent_profiles, "agents.csv")

    # Print summary statistics
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    print(f"Call Logs:       {len(call_logs)} records")
    print(f"Secure Messages: {len(secure_messages)} records")
    print(f"Case Notes:      {len(case_notes)} records")
    print(f"Agent Profiles:  {len(agent_profiles)} records")
    print("=" * 80)


if __name__ == "__main__":
    main()
