"""
Healthcare Synthetic Data Generator
====================================
Generates a realistic, interconnected synthetic dataset for health insurance
prototyping and demos. All data is fictional — no real PHI/PII.

Entity Relationship Overview:
─────────────────────────────
  Employers ──< Plans ──< Benefits
      │                      │
      └──< Members ──────────┘ (enrollment)
              │
              ├──< Dependents
              ├──< Eligibility Periods
              ├──< Claims (Medical & Pharmacy)
              │       │
              │       ├──< Claim Lines
              │       └──> Providers
              ├──< Authorizations
              └──< Accumulator (deductible/OOP tracking)

  Providers (independent entity, referenced by claims)
  Diagnosis Codes / Procedure Codes (reference data)
"""

import json
import csv
import random
import uuid
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import defaultdict

# ─── Seed for reproducibility ────────────────────────────────────────────────
random.seed(42)

# ─── Output paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
JSON_DIR = BASE_DIR / "data" / "json"
CSV_DIR = BASE_DIR / "data" / "csv"
JSON_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

# ─── Reference Data ──────────────────────────────────────────────────────────

FIRST_NAMES_M = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Christopher", "Charles", "Daniel", "Matthew",
    "Anthony", "Mark", "Donald", "Steven", "Andrew", "Paul", "Joshua",
    "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric",
    "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
    "Benjamin", "Samuel", "Raymond", "Gregory", "Frank", "Alexander",
    "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose",
    "Nathan", "Henry", "Peter", "Douglas", "Zachary", "Kyle",
]

FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily",
    "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen",
    "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma",
    "Nicole", "Helen", "Samantha", "Katherine", "Christine", "Debra",
    "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
    "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia", "Victoria",
    "Kelly", "Lauren", "Christina",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz",
    "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris",
    "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
]

STREETS = [
    "Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Elm St", "Pine Rd",
    "Walnut Blvd", "Cherry Ct", "Birch Way", "Ash Pl", "Spruce Ter",
    "Willow Dr", "Sycamore Ave", "Hickory Ln", "Poplar St", "Magnolia Blvd",
    "Cypress Rd", "Laurel Way", "Dogwood Ct", "Juniper Pl",
    "Washington Ave", "Lincoln Blvd", "Jefferson Dr", "Franklin St",
    "Madison Ln", "Park Ave", "Lake Dr", "River Rd", "Hill St",
    "Valley Way", "Sunset Blvd", "Highland Ave", "Meadow Ln",
]

CITIES_STATES = [
    ("New York", "NY", "100"), ("Los Angeles", "CA", "900"),
    ("Chicago", "IL", "606"), ("Houston", "TX", "770"),
    ("Phoenix", "AZ", "850"), ("Philadelphia", "PA", "191"),
    ("San Antonio", "TX", "782"), ("San Diego", "CA", "921"),
    ("Dallas", "TX", "752"), ("Austin", "TX", "787"),
    ("Jacksonville", "FL", "322"), ("Columbus", "OH", "432"),
    ("Charlotte", "NC", "282"), ("Indianapolis", "IN", "462"),
    ("San Francisco", "CA", "941"), ("Seattle", "WA", "981"),
    ("Denver", "CO", "802"), ("Nashville", "TN", "372"),
    ("Portland", "OR", "972"), ("Atlanta", "GA", "303"),
    ("Minneapolis", "MN", "554"), ("Tampa", "FL", "336"),
    ("Miami", "FL", "331"), ("Raleigh", "NC", "276"),
    ("Boston", "MA", "021"), ("Detroit", "MI", "482"),
]

EMPLOYER_NAMES = [
    "Acme Corporation", "GlobalTech Industries", "Meridian Healthcare Systems",
    "Pinnacle Financial Group", "Summit Manufacturing Co", "Horizon Media Group",
    "Cascade Energy Solutions", "Sterling Logistics Inc", "Vanguard Retail Corp",
    "Apex Construction LLC", "Quantum Software Solutions", "Heritage Foods International",
    "Titan Aerospace Engineering", "Coastal Hospitality Group", "Redwood Consulting Partners",
    "Atlas Transportation Co", "Beacon Education Foundation", "Ironclad Security Services",
    "Sapphire Telecommunications", "Prairie Agricultural Corp", "Metro Transit Authority",
    "Evergreen Environmental Services", "Diamond Mining Operations", "Liberty Insurance Brokers",
    "Pacific Marine Industries",
]

EMPLOYER_INDUSTRIES = [
    "Technology", "Manufacturing", "Healthcare", "Financial Services",
    "Construction", "Media", "Energy", "Logistics", "Retail",
    "Aerospace", "Hospitality", "Consulting", "Transportation",
    "Education", "Security", "Telecommunications", "Agriculture",
    "Public Sector", "Environmental Services", "Mining", "Insurance",
    "Marine", "Pharmaceutical", "Legal Services", "Real Estate",
]

PLAN_TYPES = ["HMO", "PPO", "EPO", "HDHP", "POS"]
PLAN_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
COVERAGE_TYPES = ["Individual", "Individual + Spouse", "Individual + Children", "Family"]

SPECIALTIES = [
    "Family Medicine", "Internal Medicine", "Pediatrics", "Cardiology",
    "Orthopedics", "Dermatology", "Gastroenterology", "Neurology",
    "Oncology", "Pulmonology", "Endocrinology", "Rheumatology",
    "Urology", "Ophthalmology", "OB/GYN", "Psychiatry",
    "Emergency Medicine", "Radiology", "Anesthesiology", "Pathology",
    "General Surgery", "Plastic Surgery", "ENT", "Allergy & Immunology",
    "Physical Therapy", "Occupational Therapy", "Pharmacy",
]

FACILITY_TYPES = ["Hospital", "Clinic", "Urgent Care", "Surgery Center", "Lab", "Imaging Center", "Pharmacy"]

PROVIDER_SUFFIXES = [
    "Medical Center", "Health System", "Clinic", "Medical Group",
    "Healthcare", "Medical Associates", "Health Partners",
    "Physicians Group", "Wellness Center", "Medical Practice",
]

# ICD-10 codes (subset for realism)
DIAGNOSIS_CODES = [
    {"code": "J06.9", "description": "Acute upper respiratory infection, unspecified", "category": "Respiratory"},
    {"code": "J20.9", "description": "Acute bronchitis, unspecified", "category": "Respiratory"},
    {"code": "J45.909", "description": "Unspecified asthma, uncomplicated", "category": "Respiratory"},
    {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "category": "Endocrine"},
    {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia", "category": "Endocrine"},
    {"code": "E78.5", "description": "Hyperlipidemia, unspecified", "category": "Endocrine"},
    {"code": "I10", "description": "Essential (primary) hypertension", "category": "Cardiovascular"},
    {"code": "I25.10", "description": "Atherosclerotic heart disease of native coronary artery", "category": "Cardiovascular"},
    {"code": "I48.91", "description": "Unspecified atrial fibrillation", "category": "Cardiovascular"},
    {"code": "M54.5", "description": "Low back pain", "category": "Musculoskeletal"},
    {"code": "M79.3", "description": "Panniculitis, unspecified", "category": "Musculoskeletal"},
    {"code": "M17.11", "description": "Primary osteoarthritis, right knee", "category": "Musculoskeletal"},
    {"code": "K21.0", "description": "Gastro-esophageal reflux disease with esophagitis", "category": "Digestive"},
    {"code": "K58.9", "description": "Irritable bowel syndrome without diarrhea", "category": "Digestive"},
    {"code": "F32.1", "description": "Major depressive disorder, single episode, moderate", "category": "Mental Health"},
    {"code": "F41.1", "description": "Generalized anxiety disorder", "category": "Mental Health"},
    {"code": "G43.909", "description": "Migraine, unspecified, not intractable", "category": "Neurological"},
    {"code": "N39.0", "description": "Urinary tract infection, site not specified", "category": "Genitourinary"},
    {"code": "L30.9", "description": "Dermatitis, unspecified", "category": "Dermatological"},
    {"code": "R10.9", "description": "Unspecified abdominal pain", "category": "Symptoms"},
    {"code": "R05.9", "description": "Cough, unspecified", "category": "Symptoms"},
    {"code": "Z00.00", "description": "Encounter for general adult medical examination", "category": "Preventive"},
    {"code": "Z12.31", "description": "Encounter for screening mammogram", "category": "Preventive"},
    {"code": "Z23", "description": "Encounter for immunization", "category": "Preventive"},
    {"code": "S82.001A", "description": "Unspecified fracture of right patella, initial encounter", "category": "Injury"},
    {"code": "S93.401A", "description": "Sprain of unspecified ligament of right ankle, initial", "category": "Injury"},
    {"code": "T78.40XA", "description": "Allergy, unspecified, initial encounter", "category": "Allergy"},
]

# CPT codes (subset)
PROCEDURE_CODES = [
    {"code": "99213", "description": "Office visit, established patient, moderate complexity", "category": "E&M", "avg_cost": 150},
    {"code": "99214", "description": "Office visit, established patient, high complexity", "category": "E&M", "avg_cost": 225},
    {"code": "99215", "description": "Office visit, established patient, highest complexity", "category": "E&M", "avg_cost": 325},
    {"code": "99203", "description": "Office visit, new patient, low complexity", "category": "E&M", "avg_cost": 200},
    {"code": "99204", "description": "Office visit, new patient, moderate complexity", "category": "E&M", "avg_cost": 300},
    {"code": "99281", "description": "Emergency department visit, minor", "category": "Emergency", "avg_cost": 250},
    {"code": "99283", "description": "Emergency department visit, moderate", "category": "Emergency", "avg_cost": 750},
    {"code": "99285", "description": "Emergency department visit, high severity", "category": "Emergency", "avg_cost": 2500},
    {"code": "99385", "description": "Preventive visit, new patient, 18-39 years", "category": "Preventive", "avg_cost": 275},
    {"code": "99395", "description": "Preventive visit, established patient, 18-39 years", "category": "Preventive", "avg_cost": 250},
    {"code": "99396", "description": "Preventive visit, established patient, 40-64 years", "category": "Preventive", "avg_cost": 275},
    {"code": "71046", "description": "Chest X-ray, 2 views", "category": "Radiology", "avg_cost": 150},
    {"code": "73721", "description": "MRI of knee without contrast", "category": "Radiology", "avg_cost": 1200},
    {"code": "77067", "description": "Screening mammography, bilateral", "category": "Radiology", "avg_cost": 350},
    {"code": "80053", "description": "Comprehensive metabolic panel", "category": "Lab", "avg_cost": 45},
    {"code": "85025", "description": "Complete blood count (CBC) with differential", "category": "Lab", "avg_cost": 35},
    {"code": "83036", "description": "Hemoglobin A1c", "category": "Lab", "avg_cost": 55},
    {"code": "80061", "description": "Lipid panel", "category": "Lab", "avg_cost": 50},
    {"code": "36415", "description": "Venipuncture (blood draw)", "category": "Lab", "avg_cost": 15},
    {"code": "90471", "description": "Immunization administration", "category": "Preventive", "avg_cost": 25},
    {"code": "90715", "description": "Tdap vaccine", "category": "Preventive", "avg_cost": 60},
    {"code": "96372", "description": "Therapeutic injection, subcutaneous", "category": "Procedure", "avg_cost": 75},
    {"code": "27447", "description": "Total knee replacement", "category": "Surgery", "avg_cost": 35000},
    {"code": "47562", "description": "Laparoscopic cholecystectomy", "category": "Surgery", "avg_cost": 12000},
    {"code": "43239", "description": "Upper GI endoscopy with biopsy", "category": "Procedure", "avg_cost": 3500},
    {"code": "45380", "description": "Colonoscopy with biopsy", "category": "Procedure", "avg_cost": 4000},
    {"code": "97110", "description": "Therapeutic exercises", "category": "Therapy", "avg_cost": 85},
    {"code": "97140", "description": "Manual therapy techniques", "category": "Therapy", "avg_cost": 85},
]

# ─── Clinical Coherence Maps ────────────────────────────────────────────────

DIAGNOSIS_PROCEDURE_MAP = {
    "Respiratory":      ["E&M", "Lab", "Radiology", "Emergency", "Preventive"],
    "Endocrine":        ["E&M", "Lab", "Preventive"],
    "Cardiovascular":   ["E&M", "Lab", "Radiology", "Emergency", "Procedure", "Surgery"],
    "Musculoskeletal":  ["E&M", "Radiology", "Therapy", "Surgery", "Procedure"],
    "Digestive":        ["E&M", "Lab", "Procedure", "Radiology"],
    "Mental Health":    ["E&M", "Preventive"],
    "Neurological":     ["E&M", "Lab", "Radiology"],
    "Genitourinary":    ["E&M", "Lab"],
    "Dermatological":   ["E&M", "Procedure"],
    "Symptoms":         ["E&M", "Lab", "Radiology", "Emergency"],
    "Preventive":       ["Preventive", "Lab", "E&M", "Radiology"],
    "Injury":           ["E&M", "Radiology", "Emergency", "Surgery", "Therapy"],
    "Allergy":          ["E&M", "Lab", "Emergency"],
}

DIAGNOSIS_SPECIALTY_MAP = {
    "Respiratory":      ["Family Medicine", "Internal Medicine", "Pulmonology", "Allergy & Immunology", "Emergency Medicine"],
    "Endocrine":        ["Family Medicine", "Internal Medicine", "Endocrinology"],
    "Cardiovascular":   ["Family Medicine", "Internal Medicine", "Cardiology", "Emergency Medicine"],
    "Musculoskeletal":  ["Family Medicine", "Internal Medicine", "Orthopedics", "Rheumatology", "Physical Therapy"],
    "Digestive":        ["Family Medicine", "Internal Medicine", "Gastroenterology"],
    "Mental Health":    ["Family Medicine", "Internal Medicine", "Psychiatry"],
    "Neurological":     ["Family Medicine", "Internal Medicine", "Neurology"],
    "Genitourinary":    ["Family Medicine", "Internal Medicine", "Urology", "OB/GYN"],
    "Dermatological":   ["Family Medicine", "Internal Medicine", "Dermatology"],
    "Symptoms":         ["Family Medicine", "Internal Medicine", "Emergency Medicine"],
    "Preventive":       ["Family Medicine", "Internal Medicine", "Pediatrics", "OB/GYN"],
    "Injury":           ["Family Medicine", "Internal Medicine", "Orthopedics", "Emergency Medicine", "General Surgery"],
    "Allergy":          ["Family Medicine", "Internal Medicine", "Allergy & Immunology"],
}

# NDC / pharmacy data
MEDICATIONS = [
    {"name": "Metformin 500mg", "ndc": "00093-7212-01", "category": "Diabetes", "avg_cost": 15, "days_supply": 30},
    {"name": "Metformin 1000mg", "ndc": "00093-7214-01", "category": "Diabetes", "avg_cost": 20, "days_supply": 30},
    {"name": "Lisinopril 10mg", "ndc": "00093-1044-01", "category": "Cardiovascular", "avg_cost": 12, "days_supply": 30},
    {"name": "Lisinopril 20mg", "ndc": "00093-1045-01", "category": "Cardiovascular", "avg_cost": 15, "days_supply": 30},
    {"name": "Amlodipine 5mg", "ndc": "00093-3171-01", "category": "Cardiovascular", "avg_cost": 14, "days_supply": 30},
    {"name": "Atorvastatin 20mg", "ndc": "00093-5057-01", "category": "Cardiovascular", "avg_cost": 18, "days_supply": 30},
    {"name": "Atorvastatin 40mg", "ndc": "00093-5058-01", "category": "Cardiovascular", "avg_cost": 22, "days_supply": 30},
    {"name": "Omeprazole 20mg", "ndc": "00093-5282-01", "category": "GI", "avg_cost": 16, "days_supply": 30},
    {"name": "Sertraline 50mg", "ndc": "00093-7235-01", "category": "Mental Health", "avg_cost": 14, "days_supply": 30},
    {"name": "Sertraline 100mg", "ndc": "00093-7236-01", "category": "Mental Health", "avg_cost": 18, "days_supply": 30},
    {"name": "Escitalopram 10mg", "ndc": "00093-5851-01", "category": "Mental Health", "avg_cost": 20, "days_supply": 30},
    {"name": "Albuterol Inhaler", "ndc": "00093-3174-01", "category": "Respiratory", "avg_cost": 55, "days_supply": 30},
    {"name": "Fluticasone Nasal Spray", "ndc": "00093-8122-01", "category": "Respiratory", "avg_cost": 28, "days_supply": 30},
    {"name": "Amoxicillin 500mg", "ndc": "00093-4150-01", "category": "Antibiotic", "avg_cost": 12, "days_supply": 10},
    {"name": "Azithromycin 250mg", "ndc": "00093-7169-01", "category": "Antibiotic", "avg_cost": 18, "days_supply": 5},
    {"name": "Ibuprofen 800mg", "ndc": "00093-6615-01", "category": "Pain", "avg_cost": 10, "days_supply": 30},
    {"name": "Gabapentin 300mg", "ndc": "00093-3159-01", "category": "Pain/Neuro", "avg_cost": 16, "days_supply": 30},
    {"name": "Levothyroxine 50mcg", "ndc": "00093-5552-01", "category": "Thyroid", "avg_cost": 14, "days_supply": 30},
    {"name": "Prednisone 10mg", "ndc": "00093-6340-01", "category": "Anti-inflammatory", "avg_cost": 8, "days_supply": 14},
    {"name": "Montelukast 10mg", "ndc": "00093-7390-01", "category": "Respiratory", "avg_cost": 22, "days_supply": 30},
    {"name": "Insulin Glargine 100u/mL", "ndc": "00088-2220-33", "category": "Diabetes", "avg_cost": 285, "days_supply": 30},
    {"name": "Ozempic 1mg/dose", "ndc": "00169-4132-12", "category": "Diabetes", "avg_cost": 935, "days_supply": 28},
    {"name": "Humira 40mg", "ndc": "00074-4339-02", "category": "Autoimmune", "avg_cost": 5800, "days_supply": 28},
    {"name": "Eliquis 5mg", "ndc": "00003-0894-21", "category": "Cardiovascular", "avg_cost": 520, "days_supply": 30},
]

AUTH_TYPES = ["Prior Authorization", "Pre-certification", "Concurrent Review", "Retrospective Review"]
AUTH_STATUSES = ["Approved", "Denied", "Pending", "Partially Approved", "Withdrawn"]
CLAIM_STATUSES = ["Paid", "Denied", "Pending", "Adjusted", "Appealed"]
DENIAL_REASONS = [
    "Not medically necessary",
    "Out of network provider",
    "Pre-authorization not obtained",
    "Exceeds benefit maximum",
    "Duplicate claim",
    "Non-covered service",
    "Timely filing limit exceeded",
    "Coordination of benefits",
    "Member not eligible on date of service",
]

PLACE_OF_SERVICE = [
    {"code": "11", "description": "Office"},
    {"code": "20", "description": "Urgent Care Facility"},
    {"code": "21", "description": "Inpatient Hospital"},
    {"code": "22", "description": "Outpatient Hospital"},
    {"code": "23", "description": "Emergency Room"},
    {"code": "31", "description": "Skilled Nursing Facility"},
    {"code": "81", "description": "Independent Laboratory"},
]


# ─── Helper Functions ────────────────────────────────────────────────────────

def gen_id(prefix=""):
    """Generate a short, readable ID with optional prefix."""
    uid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{uid}" if prefix else uid

def gen_npi():
    """Generate a realistic 10-digit NPI."""
    return "1" + "".join([str(random.randint(0, 9)) for _ in range(9)])

def gen_ssn_last4():
    return str(random.randint(1000, 9999))

def gen_phone():
    area = random.randint(200, 999)
    ex = random.randint(200, 999)
    num = random.randint(1000, 9999)
    return f"({area}) {ex}-{num}"

def gen_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "protonmail.com"]
    separator = random.choice([".", "_", ""])
    num = random.randint(1, 999) if random.random() > 0.5 else ""
    return f"{first.lower()}{separator}{last.lower()}{num}@{random.choice(domains)}"

def gen_address():
    num = random.randint(100, 9999)
    street = random.choice(STREETS)
    city, state, zip_prefix = random.choice(CITIES_STATES)
    zipcode = f"{zip_prefix}{random.randint(10, 99)}"
    return {
        "line1": f"{num} {street}",
        "line2": random.choice(["", "", "", f"Apt {random.randint(1,999)}", f"Suite {random.randint(100,999)}"]),
        "city": city,
        "state": state,
        "zip": zipcode,
    }

def gen_dob(min_age=18, max_age=85):
    today = date(2026, 1, 1)
    age_days = random.randint(min_age * 365, max_age * 365)
    return (today - timedelta(days=age_days)).isoformat()

def gen_date_in_range(start, end):
    """Generate random date between start and end date strings."""
    s = datetime.fromisoformat(start)
    e = datetime.fromisoformat(end)
    delta = (e - s).days
    if delta <= 0:
        return start
    return (s + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")

def money(amount):
    """Round to 2 decimal places."""
    return round(amount, 2)


# ─── Entity Generators ───────────────────────────────────────────────────────

def generate_employers(n=25):
    """Generate employer organizations."""
    employers = []
    for i in range(n):
        emp_id = gen_id("EMP-")
        addr = gen_address()
        size = random.choice(["small", "medium", "large", "enterprise"])
        size_ranges = {"small": (10, 99), "medium": (100, 499), "large": (500, 4999), "enterprise": (5000, 50000)}
        low, high = size_ranges[size]
        employers.append({
            "employer_id": emp_id,
            "name": EMPLOYER_NAMES[i] if i < len(EMPLOYER_NAMES) else f"{random.choice(LAST_NAMES)} {random.choice(['Industries', 'Corp', 'LLC', 'Inc', 'Group'])}",
            "tax_id": f"{random.randint(10,99)}-{random.randint(1000000,9999999)}",
            "industry": EMPLOYER_INDUSTRIES[i] if i < len(EMPLOYER_INDUSTRIES) else random.choice(EMPLOYER_INDUSTRIES),
            "size_category": size,
            "employee_count": random.randint(low, high),
            "address": addr,
            "phone": gen_phone(),
            "effective_date": f"{random.randint(2018, 2024)}-01-01",
            "status": random.choices(["Active", "Active", "Active", "Terminated"], weights=[80, 10, 5, 5])[0],
            "account_manager": f"{random.choice(FIRST_NAMES_F + FIRST_NAMES_M)} {random.choice(LAST_NAMES)}",
        })
    return employers


def generate_plans(employers):
    """Generate benefit plans tied to employers."""
    plans = []
    for emp in employers:
        if emp["status"] == "Terminated":
            continue
        num_plans = random.randint(1, 3)
        for _ in range(num_plans):
            plan_type = random.choice(PLAN_TYPES)
            tier = random.choice(PLAN_TIERS)
            plan_id = gen_id("PLN-")

            # Realistic deductible/OOP based on tier
            tier_params = {
                "Bronze": {"ded_ind": (3000, 7000), "ded_fam": (6000, 14000), "oop_ind": (7000, 9100), "oop_fam": (14000, 18200), "premium_ind": (200, 350)},
                "Silver": {"ded_ind": (1500, 4000), "ded_fam": (3000, 8000), "oop_ind": (5000, 8000), "oop_fam": (10000, 16000), "premium_ind": (350, 550)},
                "Gold":   {"ded_ind": (500, 2000), "ded_fam": (1000, 4000), "oop_ind": (3000, 6000), "oop_fam": (6000, 12000), "premium_ind": (550, 800)},
                "Platinum": {"ded_ind": (0, 500), "ded_fam": (0, 1000), "oop_ind": (1000, 4000), "oop_fam": (2000, 8000), "premium_ind": (800, 1200)},
            }
            params = tier_params[tier]

            ded_ind = random.randrange(params["ded_ind"][0], params["ded_ind"][1], 250)
            ded_fam = random.randrange(params["ded_fam"][0], params["ded_fam"][1], 500)
            oop_ind = random.randrange(params["oop_ind"][0], params["oop_ind"][1], 500)
            oop_fam = random.randrange(params["oop_fam"][0], params["oop_fam"][1], 500)

            plans.append({
                "plan_id": plan_id,
                "employer_id": emp["employer_id"],
                "plan_name": f"{emp['name']} {tier} {plan_type}",
                "plan_type": plan_type,
                "tier": tier,
                "effective_date": emp["effective_date"],
                "termination_date": None,
                "status": "Active",
                "deductible_individual": ded_ind,
                "deductible_family": ded_fam,
                "out_of_pocket_max_individual": oop_ind,
                "out_of_pocket_max_family": oop_fam,
                "monthly_premium_individual": random.randrange(params["premium_ind"][0], params["premium_ind"][1], 25),
                "monthly_premium_family": None,  # computed below
                "coinsurance_in_network": random.choice([80, 80, 90, 70]),
                "coinsurance_out_of_network": random.choice([50, 60, 70]),
                "copay_pcp": random.choice([20, 25, 30, 35, 40]),
                "copay_specialist": random.choice([40, 50, 60, 75]),
                "copay_er": random.choice([150, 200, 250, 300, 350]),
                "copay_urgent_care": random.choice([50, 75, 100]),
                "copay_rx_generic": random.choice([5, 10, 15]),
                "copay_rx_preferred_brand": random.choice([30, 40, 50]),
                "copay_rx_non_preferred": random.choice([60, 75, 100]),
                "copay_rx_specialty": random.choice([150, 200, 250, 300]),
                "network_name": f"{random.choice(['Blue', 'Premier', 'Choice', 'Select', 'Preferred'])} {random.choice(['Care', 'Health', 'Network', 'Access'])}",
                "pharmacy_benefit_manager": random.choice(["Express Scripts", "CVS Caremark", "OptumRx", "MedImpact"]),
            })
            plans[-1]["monthly_premium_family"] = money(plans[-1]["monthly_premium_individual"] * random.uniform(2.5, 3.5))

    return plans


def generate_benefits(plans):
    """Generate detailed benefit schedules for each plan."""
    benefits = []
    benefit_categories = [
        ("Preventive Care", "In-Network", "$0 copay", "Covered at 100%", "Annual wellness, immunizations, screenings"),
        ("Primary Care Visit", "In-Network", "Copay", "After deductible", "Office visits with PCP"),
        ("Specialist Visit", "In-Network", "Copay", "After deductible", "Office visits with specialists"),
        ("Emergency Room", "In-Network", "Copay + Coinsurance", "After deductible", "Emergency services, waived if admitted"),
        ("Urgent Care", "In-Network", "Copay", "After deductible", "Urgent care facility visits"),
        ("Inpatient Hospital", "In-Network", "Coinsurance", "After deductible", "Room, board, and related services"),
        ("Outpatient Surgery", "In-Network", "Coinsurance", "After deductible", "Ambulatory surgery center or hospital"),
        ("Mental Health Outpatient", "In-Network", "Copay", "After deductible", "Individual and group therapy"),
        ("Mental Health Inpatient", "In-Network", "Coinsurance", "After deductible", "Inpatient psychiatric facility"),
        ("Prescription Drugs - Generic", "In-Network", "Copay", "After deductible", "Tier 1 formulary drugs"),
        ("Prescription Drugs - Brand", "In-Network", "Copay", "After deductible", "Tier 2 formulary drugs"),
        ("Prescription Drugs - Specialty", "In-Network", "Copay/Coinsurance", "After deductible", "Tier 4 specialty drugs"),
        ("Lab & Diagnostics", "In-Network", "Coinsurance", "After deductible", "Blood work, urinalysis, pathology"),
        ("Imaging", "In-Network", "Coinsurance", "After deductible", "X-ray, MRI, CT scan, ultrasound"),
        ("Physical Therapy", "In-Network", "Copay", "After deductible", "Up to 30 visits per year"),
        ("Durable Medical Equipment", "In-Network", "Coinsurance", "After deductible", "Wheelchairs, CPAP, etc."),
        ("Telehealth", "In-Network", "Copay", "$0-$25", "Virtual visits with providers"),
        ("Chiropractic", "In-Network", "Copay", "After deductible", "Up to 20 visits per year"),
    ]

    for plan in plans:
        for cat, network, cost_share, applies, desc in benefit_categories:
            benefits.append({
                "benefit_id": gen_id("BEN-"),
                "plan_id": plan["plan_id"],
                "category": cat,
                "network_tier": network,
                "cost_sharing_type": cost_share,
                "deductible_applies": applies,
                "description": desc,
                "annual_limit": None if "Preventive" in cat else random.choice([None, None, None, 30, 60]),
                "requires_auth": cat in ["Inpatient Hospital", "Outpatient Surgery", "Mental Health Inpatient", "Durable Medical Equipment", "Prescription Drugs - Specialty"],
                "requires_referral": plan["plan_type"] == "HMO" and cat in ["Specialist Visit", "Physical Therapy", "Chiropractic"],
            })
    return benefits


def _make_provider(specialty, is_facility, city, state, zip_prefix):
    """Create a single provider record with a specific location."""
    addr = {
        "line1": f"{random.randint(100, 9999)} {random.choice(STREETS)}",
        "line2": random.choice(["", "", "", f"Apt {random.randint(1,999)}", f"Suite {random.randint(100,999)}"]),
        "city": city,
        "state": state,
        "zip": f"{zip_prefix}{random.randint(10, 99)}",
    }

    if is_facility:
        hospital_names = ["St. Marys", "Memorial", "Regional", "University", "Community", "Baptist", "Methodist", "Presbyterian", "Good Samaritan", "Mercy"]
        name = f"{city} {random.choice(PROVIDER_SUFFIXES)}" if random.random() > 0.5 else f"{random.choice(hospital_names)} {specialty}"
    else:
        gender = random.choice(["M", "F"])
        first = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES)
        suffix = random.choice(["MD", "MD", "MD", "DO", "NP", "PA"])
        name = f"{first} {last}, {suffix}"

    return {
        "provider_id": gen_id("PRV-"),
        "npi": gen_npi(),
        "name": name,
        "type": "Facility" if is_facility else "Individual",
        "specialty": specialty,
        "tax_id": f"{random.randint(10,99)}-{random.randint(1000000,9999999)}",
        "address": addr,
        "phone": gen_phone(),
        "accepting_new_patients": random.random() > 0.15,
        "network_status": random.choices(["In-Network", "In-Network", "Out-of-Network"], weights=[70, 20, 10])[0],
        "languages": random.sample(["English", "Spanish", "Mandarin", "Vietnamese", "Korean", "French", "Arabic", "Hindi", "Tagalog"], k=random.randint(1, 3)),
        "rating": round(random.uniform(3.0, 5.0), 1),
        "effective_date": f"{random.randint(2015, 2024)}-{random.randint(1,12):02d}-01",
    }


def generate_providers(n=300):
    """Generate healthcare providers with guaranteed per-state coverage.

    Seeds each state with minimum PCP, facility, and specialist coverage
    to ensure clinical coherence constraints can be satisfied, then fills
    the remainder randomly.
    """
    providers = []

    # Guaranteed per-state: 2 Family Med, 1 Internal Med, 1 Hospital, 1 Lab,
    # plus 3 common specialists that cover all diagnosis categories
    common_specialists = ["Cardiology", "Orthopedics", "Emergency Medicine"]
    seed_specs = [
        ("Family Medicine", False),
        ("Family Medicine", False),
        ("Internal Medicine", False),
        ("Hospital", True),
        ("Lab", True),
    ] + [(s, False) for s in common_specialists]

    for city, state, zip_prefix in CITIES_STATES:
        for specialty, is_facility in seed_specs:
            providers.append(_make_provider(specialty, is_facility, city, state, zip_prefix))

    # Fill remaining slots with random providers
    remaining = n - len(providers)
    for _ in range(max(0, remaining)):
        is_facility = random.random() < 0.25
        city, state, zip_prefix = random.choice(CITIES_STATES)

        if is_facility:
            specialty = random.choice(FACILITY_TYPES)
        else:
            specialty = random.choice(SPECIALTIES)

        providers.append(_make_provider(specialty, is_facility, city, state, zip_prefix))

    return providers


def generate_members(n=2000, employers=None, plans=None):
    """Generate member/subscriber records with dependents."""
    members = []
    dependents = []
    eligibility_periods = []

    # Pre-compute employer-plan mapping
    emp_plans = defaultdict(list)
    for p in plans:
        emp_plans[p["employer_id"]].append(p)

    active_employers = [e for e in employers if e["status"] == "Active" and emp_plans[e["employer_id"]]]

    for i in range(n):
        gender = random.choice(["M", "F"])
        first = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES)

        # Assign to employer and plan
        emp = random.choice(active_employers)
        available_plans = emp_plans[emp["employer_id"]]
        plan = random.choice(available_plans)

        dob = gen_dob(min_age=22, max_age=68)
        age = 2026 - int(dob[:4])
        addr = gen_address()
        coverage = random.choices(COVERAGE_TYPES, weights=[40, 25, 15, 20])[0]

        member_id = gen_id("MBR-")
        subscriber_id = f"SUB{random.randint(100000000, 999999999)}"

        # Chronic conditions (for generating realistic claims later)
        chronic_conditions = []
        if random.random() < 0.15:  # ~15% have hypertension
            chronic_conditions.append("hypertension")
        if random.random() < 0.10:  # ~10% have diabetes
            chronic_conditions.append("diabetes")
        if random.random() < 0.08:  # ~8% have hyperlipidemia
            chronic_conditions.append("hyperlipidemia")
        if random.random() < 0.07:  # ~7% have asthma
            chronic_conditions.append("asthma")
        if random.random() < 0.06:  # ~6% have depression/anxiety
            chronic_conditions.append("mental_health")
        if random.random() < 0.05:  # ~5% have GERD
            chronic_conditions.append("gerd")
        if random.random() < 0.04:  # ~4% have back pain
            chronic_conditions.append("back_pain")

        member = {
            "member_id": member_id,
            "subscriber_id": subscriber_id,
            "employer_id": emp["employer_id"],
            "plan_id": plan["plan_id"],
            "first_name": first,
            "last_name": last,
            "date_of_birth": dob,
            "age": age,
            "gender": gender,
            "ssn_last4": gen_ssn_last4(),
            "email": gen_email(first, last),
            "phone": gen_phone(),
            "address": addr,
            "coverage_type": coverage,
            "relationship": "Self",
            "pcp_provider_id": None,  # assigned after providers generated
            "status": random.choices(["Active", "Active", "Active", "COBRA", "Terminated"], weights=[80, 10, 5, 3, 2])[0],
            "enrollment_date": gen_date_in_range(emp["effective_date"], "2025-06-01"),
            "termination_date": None,
            "chronic_conditions": chronic_conditions,
        }
        members.append(member)

        # Eligibility periods
        eff_start = member["enrollment_date"]
        eligibility_periods.append({
            "eligibility_id": gen_id("ELG-"),
            "member_id": member_id,
            "plan_id": plan["plan_id"],
            "coverage_type": coverage,
            "effective_date": eff_start,
            "termination_date": None if member["status"] in ["Active", "COBRA"] else gen_date_in_range(eff_start, "2025-12-31"),
            "status": member["status"],
            "cobra_flag": member["status"] == "COBRA",
        })

        # Generate dependents
        if coverage != "Individual":
            dep_last = last
            if coverage in ["Individual + Spouse", "Family"]:
                sp_gender = "F" if gender == "M" else "M"
                sp_first = random.choice(FIRST_NAMES_F if sp_gender == "F" else FIRST_NAMES_M)
                dep_id = gen_id("MBR-")
                dependents.append({
                    "member_id": dep_id,
                    "subscriber_id": subscriber_id,
                    "subscriber_member_id": member_id,
                    "employer_id": emp["employer_id"],
                    "plan_id": plan["plan_id"],
                    "first_name": sp_first,
                    "last_name": dep_last,
                    "date_of_birth": gen_dob(min_age=max(22, age - 10), max_age=min(70, age + 10)),
                    "gender": sp_gender,
                    "relationship": "Spouse",
                    "status": member["status"],
                    "enrollment_date": member["enrollment_date"],
                })
                eligibility_periods.append({
                    "eligibility_id": gen_id("ELG-"),
                    "member_id": dep_id,
                    "plan_id": plan["plan_id"],
                    "coverage_type": coverage,
                    "effective_date": member["enrollment_date"],
                    "termination_date": None if member["status"] in ["Active", "COBRA"] else gen_date_in_range(eff_start, "2025-12-31"),
                    "status": member["status"],
                    "cobra_flag": member["status"] == "COBRA",
                })

            if coverage in ["Individual + Children", "Family"]:
                num_children = random.randint(1, 3)
                for _ in range(num_children):
                    ch_gender = random.choice(["M", "F"])
                    ch_first = random.choice(FIRST_NAMES_M if ch_gender == "M" else FIRST_NAMES_F)
                    ch_id = gen_id("MBR-")
                    dependents.append({
                        "member_id": ch_id,
                        "subscriber_id": subscriber_id,
                        "subscriber_member_id": member_id,
                        "employer_id": emp["employer_id"],
                        "plan_id": plan["plan_id"],
                        "first_name": ch_first,
                        "last_name": dep_last,
                        "date_of_birth": gen_dob(min_age=1, max_age=min(25, age - 18)),
                        "gender": ch_gender,
                        "relationship": "Child",
                        "status": member["status"],
                        "enrollment_date": member["enrollment_date"],
                    })
                    eligibility_periods.append({
                        "eligibility_id": gen_id("ELG-"),
                        "member_id": ch_id,
                        "plan_id": plan["plan_id"],
                        "coverage_type": coverage,
                        "effective_date": member["enrollment_date"],
                        "termination_date": None if member["status"] in ["Active", "COBRA"] else gen_date_in_range(eff_start, "2025-12-31"),
                        "status": member["status"],
                        "cobra_flag": member["status"] == "COBRA",
                    })

    return members, dependents, eligibility_periods


def assign_pcps(members, providers):
    """Assign PCP providers to members (same state, age-appropriate specialty)."""
    pcp_all = [p for p in providers if p["type"] == "Individual" and
               p["specialty"] in ("Family Medicine", "Internal Medicine", "Pediatrics")]

    # Pre-index by state
    pcp_by_state = defaultdict(list)
    for p in pcp_all:
        pcp_by_state[p["address"]["state"]].append(p)

    for member in members:
        if random.random() < 0.1:  # 10% have no PCP
            continue
        state = member["address"]["state"]
        pool = pcp_by_state.get(state, [])
        if not pool:
            continue  # No same-state PCP available; skip rather than assign wrong state
        # Adults shouldn't have pediatrician PCP
        if member["age"] >= 18:
            adult_pool = [p for p in pool if p["specialty"] != "Pediatrics"]
            if not adult_pool:
                continue  # No adult-appropriate PCP in this state
            pool = adult_pool
        if pool:
            member["pcp_provider_id"] = random.choice(pool)["provider_id"]


def generate_medical_claims(members, dependents, providers, plans):
    """Generate realistic medical claims with clinical coherence constraints.

    Constraints applied:
    - Providers are in the same state as the member
    - Provider specialty matches the diagnosis category
    - Procedures are compatible with the diagnosis category
    - Place of service is consistent with the procedure type
    """
    claims = []
    claim_lines = []

    plan_lookup = {p["plan_id"]: p for p in plans}

    # Build subscriber address lookup for dependents (who lack their own address)
    subscriber_addr = {m["member_id"]: m["address"] for m in members}
    all_members = members + [
        {**d, "chronic_conditions": [], "age": 2026 - int(d["date_of_birth"][:4]),
         "address": subscriber_addr.get(d.get("subscriber_member_id"), {"state": "TX"})}
        for d in dependents
    ]

    pcp_providers = [p for p in providers if p["specialty"] in ["Family Medicine", "Internal Medicine"] and p["type"] == "Individual"]
    specialist_providers = [p for p in providers if p["type"] == "Individual" and p["specialty"] not in ["Family Medicine", "Internal Medicine", "Pediatrics"]]
    facility_providers = [p for p in providers if p["type"] == "Facility"]
    lab_providers = [p for p in providers if p["specialty"] in ["Lab", "Pathology"] or p["type"] == "Facility"]

    # Build state-indexed provider pools
    pcp_by_state = defaultdict(list)
    specialist_by_state = defaultdict(list)
    facility_by_state = defaultdict(list)
    lab_by_state = defaultdict(list)

    for p in pcp_providers:
        pcp_by_state[p["address"]["state"]].append(p)
    for p in specialist_providers:
        specialist_by_state[p["address"]["state"]].append(p)
    for p in facility_providers:
        facility_by_state[p["address"]["state"]].append(p)
    for p in lab_providers:
        lab_by_state[p["address"]["state"]].append(p)

    # Pre-compute compatible procedure lists per diagnosis category
    all_proc_categories = list({p["category"] for p in PROCEDURE_CODES})
    compatible_procs_cache = {}
    for dx_cat, proc_cats in DIAGNOSIS_PROCEDURE_MAP.items():
        compatible_procs_cache[dx_cat] = [p for p in PROCEDURE_CODES if p["category"] in proc_cats]

    for member in all_members:
        if member.get("status") == "Terminated":
            continue

        plan = plan_lookup.get(member["plan_id"])
        if not plan:
            continue

        member_state = member["address"]["state"]

        # Determine number of claims based on age and chronic conditions
        base_claims = random.randint(1, 4)
        chronic_bonus = len(member.get("chronic_conditions", [])) * random.randint(1, 3)
        age_bonus = 1 if member["age"] > 50 else 0
        num_claims = min(base_claims + chronic_bonus + age_bonus, 15)

        for _ in range(num_claims):
            claim_id = gen_id("CLM-")
            service_date = gen_date_in_range("2025-01-01", "2025-12-31")

            # 1. Select diagnosis FIRST (before provider)
            chronics = member.get("chronic_conditions", [])
            if chronics and random.random() < 0.6:
                condition = random.choice(chronics)
                condition_map = {
                    "hypertension": [d for d in DIAGNOSIS_CODES if d["category"] == "Cardiovascular"],
                    "diabetes": [d for d in DIAGNOSIS_CODES if d["category"] == "Endocrine"],
                    "hyperlipidemia": [d for d in DIAGNOSIS_CODES if d["code"] == "E78.5"],
                    "asthma": [d for d in DIAGNOSIS_CODES if d["code"] == "J45.909"],
                    "mental_health": [d for d in DIAGNOSIS_CODES if d["category"] == "Mental Health"],
                    "gerd": [d for d in DIAGNOSIS_CODES if d["code"] == "K21.0"],
                    "back_pain": [d for d in DIAGNOSIS_CODES if d["code"] == "M54.5"],
                }
                dx_pool = condition_map.get(condition, DIAGNOSIS_CODES)
                primary_dx = random.choice(dx_pool) if dx_pool else random.choice(DIAGNOSIS_CODES)
            else:
                primary_dx = random.choice(DIAGNOSIS_CODES)

            dx_category = primary_dx["category"]
            compatible_specialties = DIAGNOSIS_SPECIALTY_MAP.get(dx_category, SPECIALTIES)

            # 2. Select provider filtered by state + specialty compatibility
            #    Fallback: same-state+compatible > same-state-any > compatible-any-state > global
            claim_type_roll = random.random()
            if claim_type_roll < 0.50:
                # Professional — PCP or specialist
                state_pool = pcp_by_state.get(member_state, []) + specialist_by_state.get(member_state, [])
                pool = [p for p in state_pool if p["specialty"] in compatible_specialties]
                if not pool:  # fallback: same state, any specialty
                    pool = state_pool
                if not pool:  # fallback: compatible specialty, any state
                    pool = [p for p in pcp_providers + specialist_providers if p["specialty"] in compatible_specialties]
                provider = random.choice(pool) if pool else random.choice(pcp_providers + specialist_providers)
                claim_type = "Professional"
            elif claim_type_roll < 0.80:
                # Specialist — prefer compatible specialist in-state, fall back to PCP in-state
                state_pool = specialist_by_state.get(member_state, [])
                pool = [p for p in state_pool if p["specialty"] in compatible_specialties]
                if not pool:  # fallback: same state PCP (Family Med/Internal Med handle most things)
                    pool = [p for p in pcp_by_state.get(member_state, []) if p["specialty"] in compatible_specialties]
                if not pool:  # fallback: same state, any specialist
                    pool = state_pool
                if not pool:  # fallback: compatible specialty, any state
                    pool = [p for p in specialist_providers if p["specialty"] in compatible_specialties]
                provider = random.choice(pool) if pool else random.choice(specialist_providers) if specialist_providers else random.choice(providers)
                claim_type = "Professional"
            elif claim_type_roll < 0.92:
                # Institutional — same state facility (skip specialty filter, hospitals treat everything)
                pool = facility_by_state.get(member_state, [])
                provider = random.choice(pool) if pool else random.choice(facility_providers) if facility_providers else random.choice(providers)
                claim_type = "Institutional"
            else:
                # Lab — same state
                pool = lab_by_state.get(member_state, [])
                provider = random.choice(pool) if pool else random.choice(lab_providers) if lab_providers else random.choice(providers)
                claim_type = "Professional"

            # 3. Select procedures compatible with diagnosis
            compatible_procs = compatible_procs_cache.get(dx_category, PROCEDURE_CODES)
            if not compatible_procs:
                compatible_procs = PROCEDURE_CODES

            # Generate claim lines
            num_lines = random.choices([1, 2, 3, 4], weights=[50, 30, 15, 5])[0]
            total_billed = 0
            total_allowed = 0
            total_paid = 0
            total_member_resp = 0
            lines = []

            for line_num in range(1, num_lines + 1):
                proc = random.choice(compatible_procs)
                billed = money(proc["avg_cost"] * random.uniform(0.8, 1.5))
                allowed = money(billed * random.uniform(0.5, 0.85))
                coinsurance_pct = plan["coinsurance_in_network"] / 100 if provider["network_status"] == "In-Network" else plan["coinsurance_out_of_network"] / 100
                plan_paid = money(allowed * coinsurance_pct)
                member_resp = money(allowed - plan_paid)

                total_billed += billed
                total_allowed += allowed
                total_paid += plan_paid
                total_member_resp += member_resp

                lines.append({
                    "claim_line_id": gen_id("CLL-"),
                    "claim_id": claim_id,
                    "line_number": line_num,
                    "procedure_code": proc["code"],
                    "procedure_description": proc["description"],
                    "modifier": random.choice([None, None, None, "25", "59", "76"]),
                    "units": random.choices([1, 1, 1, 2, 3], weights=[60, 20, 10, 5, 5])[0],
                    "diagnosis_pointer": "1",
                    "billed_amount": billed,
                    "allowed_amount": allowed,
                    "plan_paid_amount": plan_paid,
                    "member_responsibility": member_resp,
                    "service_date": service_date,
                })
                claim_lines.extend(lines[-1:])

            # 4. Set place of service consistent with claim context
            first_proc_cat = lines[0]["procedure_code"] if lines else None
            first_proc = next((p for p in PROCEDURE_CODES if p["code"] == first_proc_cat), None) if first_proc_cat else None
            has_emergency = any(
                next((p for p in PROCEDURE_CODES if p["code"] == ln["procedure_code"]), {}).get("category") == "Emergency"
                for ln in lines
            )

            if has_emergency:
                pos = next(p for p in PLACE_OF_SERVICE if p["code"] == "23")  # ER
            elif claim_type == "Institutional":
                pos = random.choice([p for p in PLACE_OF_SERVICE if p["code"] in ["21", "22"]])
            elif claim_type_roll >= 0.92:  # Lab
                pos = next(p for p in PLACE_OF_SERVICE if p["code"] == "81")
            else:
                pos = next(p for p in PLACE_OF_SERVICE if p["code"] == "11")  # Office

            # Claim status
            status = random.choices(CLAIM_STATUSES, weights=[70, 8, 12, 7, 3])[0]

            claim = {
                "claim_id": claim_id,
                "member_id": member["member_id"],
                "plan_id": member["plan_id"],
                "provider_id": provider["provider_id"],
                "claim_type": claim_type,
                "claim_status": status,
                "service_date": service_date,
                "received_date": gen_date_in_range(service_date, (datetime.fromisoformat(service_date) + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")),
                "processed_date": gen_date_in_range(service_date, (datetime.fromisoformat(service_date) + timedelta(days=random.randint(7, 60))).strftime("%Y-%m-%d")) if status != "Pending" else None,
                "primary_diagnosis": primary_dx["code"],
                "primary_diagnosis_description": primary_dx["description"],
                "secondary_diagnosis": random.choice(DIAGNOSIS_CODES)["code"] if random.random() < 0.3 else None,
                "place_of_service": pos["code"],
                "place_of_service_description": pos["description"],
                "total_billed": money(total_billed),
                "total_allowed": money(total_allowed),
                "total_plan_paid": money(total_paid),
                "total_member_responsibility": money(total_member_resp),
                "denial_reason": random.choice(DENIAL_REASONS) if status == "Denied" else None,
                "appeal_status": random.choice(["Pending", "Upheld", "Overturned"]) if status == "Appealed" else None,
                "check_number": f"CHK{random.randint(100000, 999999)}" if status == "Paid" else None,
                "payment_date": gen_date_in_range(service_date, (datetime.fromisoformat(service_date) + timedelta(days=random.randint(14, 90))).strftime("%Y-%m-%d")) if status == "Paid" else None,
            }
            claims.append(claim)

    return claims, claim_lines


def generate_pharmacy_claims(members, dependents, plans):
    """Generate pharmacy/prescription claims."""
    rx_claims = []
    plan_lookup = {p["plan_id"]: p for p in plans}

    all_members = members + [
        {**d, "chronic_conditions": [], "age": 2026 - int(d["date_of_birth"][:4])}
        for d in dependents
    ]

    for member in all_members:
        if member.get("status") == "Terminated":
            continue

        plan = plan_lookup.get(member["plan_id"])
        if not plan:
            continue

        chronics = member.get("chronic_conditions", [])
        meds_for_member = []

        # Assign meds based on chronic conditions
        condition_meds = {
            "hypertension": [m for m in MEDICATIONS if m["category"] == "Cardiovascular"],
            "diabetes": [m for m in MEDICATIONS if m["category"] == "Diabetes"],
            "hyperlipidemia": [m for m in MEDICATIONS if "statin" in m["name"].lower() or m["name"].startswith("Atorvastatin")],
            "asthma": [m for m in MEDICATIONS if m["category"] == "Respiratory"],
            "mental_health": [m for m in MEDICATIONS if m["category"] == "Mental Health"],
            "gerd": [m for m in MEDICATIONS if m["name"].startswith("Omeprazole")],
            "back_pain": [m for m in MEDICATIONS if m["category"] in ["Pain", "Pain/Neuro"]],
        }

        for condition in chronics:
            pool = condition_meds.get(condition, [])
            if pool:
                meds_for_member.append(random.choice(pool))

        # Random acute meds
        if random.random() < 0.3:
            meds_for_member.append(random.choice([m for m in MEDICATIONS if m["category"] == "Antibiotic"]))
        if random.random() < 0.15:
            meds_for_member.append(random.choice(MEDICATIONS))

        # Generate fills for each med (quarterly refills for chronic)
        for med in meds_for_member:
            is_chronic = med["category"] not in ["Antibiotic", "Anti-inflammatory"]
            num_fills = random.randint(3, 4) if is_chronic else 1

            for fill_num in range(num_fills):
                fill_date = gen_date_in_range(
                    f"2025-{fill_num * 3 + 1:02d}-01" if fill_num < 4 else "2025-10-01",
                    f"2025-{min(fill_num * 3 + 3, 12):02d}-28"
                )

                ingredient_cost = money(med["avg_cost"] * random.uniform(0.8, 1.3))
                dispensing_fee = money(random.uniform(1.50, 3.50))
                total_cost = money(ingredient_cost + dispensing_fee)

                # Copay based on drug tier
                if med["avg_cost"] < 30:
                    copay = plan["copay_rx_generic"]
                elif med["avg_cost"] < 200:
                    copay = plan["copay_rx_preferred_brand"]
                elif med["avg_cost"] < 500:
                    copay = plan["copay_rx_non_preferred"]
                else:
                    copay = plan["copay_rx_specialty"]

                plan_paid = money(max(0, total_cost - copay))

                rx_claims.append({
                    "rx_claim_id": gen_id("RXC-"),
                    "member_id": member["member_id"],
                    "plan_id": member["plan_id"],
                    "fill_date": fill_date,
                    "medication_name": med["name"],
                    "ndc": med["ndc"],
                    "medication_category": med["category"],
                    "quantity": random.choice([30, 60, 90]) if is_chronic else med["days_supply"],
                    "days_supply": med["days_supply"],
                    "refill_number": fill_num,
                    "prescriber_npi": gen_npi(),
                    "pharmacy_npi": gen_npi(),
                    "pharmacy_name": f"{random.choice(['CVS', 'Walgreens', 'Rite Aid', 'Walmart', 'Costco', 'Kroger', 'Publix'])} Pharmacy #{random.randint(1000, 9999)}",
                    "formulary_status": random.choices(["Preferred", "Preferred", "Non-Preferred", "Specialty"], weights=[50, 25, 15, 10])[0],
                    "prior_auth_required": med["avg_cost"] > 200,
                    "ingredient_cost": ingredient_cost,
                    "dispensing_fee": dispensing_fee,
                    "total_cost": total_cost,
                    "member_copay": copay,
                    "plan_paid": plan_paid,
                    "claim_status": random.choices(["Paid", "Paid", "Reversed", "Pending"], weights=[80, 10, 5, 5])[0],
                    "daw_code": random.choice(["0", "0", "0", "1", "2"]),  # Dispense As Written
                })

    return rx_claims


def generate_authorizations(members, providers, plans):
    """Generate prior authorization records."""
    auths = []
    plan_lookup = {p["plan_id"]: p for p in plans}

    auth_services = [
        ("Knee Replacement Surgery", "27447", "Surgery", 14),
        ("MRI - Lower Extremity", "73721", "Imaging", 7),
        ("Colonoscopy", "45380", "Procedure", 7),
        ("Inpatient Admission", "99223", "Inpatient", 30),
        ("Physical Therapy (20 visits)", "97110", "Therapy", 90),
        ("Specialty Medication - Humira", "J0135", "Pharmacy", 180),
        ("Specialty Medication - Ozempic", "J3490", "Pharmacy", 90),
        ("Outpatient Surgery - Cholecystectomy", "47562", "Surgery", 14),
        ("Home Health Services", "99600", "Home Health", 60),
        ("DME - CPAP Machine", "E0601", "DME", 365),
    ]

    # Only ~15% of members need auths
    auth_members = random.sample(members, k=min(int(len(members) * 0.15), len(members)))

    for member in auth_members:
        plan = plan_lookup.get(member["plan_id"])
        if not plan:
            continue

        num_auths = random.randint(1, 3)
        for _ in range(num_auths):
            service = random.choice(auth_services)
            request_date = gen_date_in_range("2025-01-01", "2025-12-31")
            status = random.choices(AUTH_STATUSES, weights=[55, 15, 15, 10, 5])[0]

            auths.append({
                "auth_id": gen_id("AUTH-"),
                "member_id": member["member_id"],
                "plan_id": member["plan_id"],
                "provider_id": random.choice(providers)["provider_id"],
                "auth_type": random.choice(AUTH_TYPES),
                "service_description": service[0],
                "procedure_code": service[1],
                "service_category": service[2],
                "status": status,
                "request_date": request_date,
                "decision_date": gen_date_in_range(request_date, (datetime.fromisoformat(request_date) + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d")) if status != "Pending" else None,
                "effective_date": request_date if status in ["Approved", "Partially Approved"] else None,
                "expiration_date": (datetime.fromisoformat(request_date) + timedelta(days=service[3])).strftime("%Y-%m-%d") if status in ["Approved", "Partially Approved"] else None,
                "approved_units": random.randint(1, 20) if status in ["Approved", "Partially Approved"] else None,
                "requested_units": random.randint(1, 30),
                "denial_reason": random.choice(DENIAL_REASONS[:3]) if status == "Denied" else None,
                "clinical_notes": f"Clinical review {'completed' if status != 'Pending' else 'in progress'} for {service[0].lower()}",
                "urgency": random.choices(["Standard", "Standard", "Urgent", "Emergency"], weights=[50, 30, 15, 5])[0],
                "reviewer": f"Dr. {random.choice(FIRST_NAMES_F + FIRST_NAMES_M)} {random.choice(LAST_NAMES)}",
            })

    return auths


def generate_accumulators(members, claims, plan_lookup):
    """Generate deductible/OOP accumulator tracking."""
    accumulators = []
    member_accums = defaultdict(lambda: {"deductible_used": 0, "oop_used": 0})

    for claim in claims:
        if claim["claim_status"] == "Paid":
            mid = claim["member_id"]
            member_accums[mid]["deductible_used"] += claim.get("total_member_responsibility", 0)
            member_accums[mid]["oop_used"] += claim.get("total_member_responsibility", 0)

    for member in members:
        plan = plan_lookup.get(member["plan_id"])
        if not plan:
            continue

        accum = member_accums[member["member_id"]]
        accumulators.append({
            "accumulator_id": gen_id("ACC-"),
            "member_id": member["member_id"],
            "plan_id": member["plan_id"],
            "plan_year": 2025,
            "deductible_limit": plan["deductible_individual"],
            "deductible_used": money(min(accum["deductible_used"], plan["deductible_individual"])),
            "deductible_remaining": money(max(0, plan["deductible_individual"] - accum["deductible_used"])),
            "oop_max_limit": plan["out_of_pocket_max_individual"],
            "oop_used": money(min(accum["oop_used"], plan["out_of_pocket_max_individual"])),
            "oop_remaining": money(max(0, plan["out_of_pocket_max_individual"] - accum["oop_used"])),
            "last_updated": "2025-12-31",
        })

    return accumulators


# ─── Export Functions ─────────────────────────────────────────────────────────

def save_json(data, filename):
    filepath = JSON_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ {filepath} ({len(data)} records)")

def save_csv(data, filename):
    if not data:
        return
    filepath = CSV_DIR / filename
    # Flatten nested dicts
    flat_data = []
    for row in data:
        flat = {}
        for k, v in row.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    flat[f"{k}_{k2}"] = v2
            elif isinstance(v, list):
                flat[k] = "; ".join(str(x) for x in v)
            else:
                flat[k] = v
        flat_data.append(flat)

    fieldnames = list(flat_data[0].keys())
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_data)
    print(f"  ✓ {filepath} ({len(data)} records)")


# ─── Main Generation Pipeline ────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Healthcare Synthetic Data Generator")
    print("=" * 60)
    print()

    print("Phase 1: Generating reference entities...")
    employers = generate_employers(25)
    print(f"  → {len(employers)} employers")

    plans = generate_plans(employers)
    print(f"  → {len(plans)} benefit plans")

    benefits = generate_benefits(plans)
    print(f"  → {len(benefits)} benefit line items")

    providers = generate_providers(300)
    print(f"  → {len(providers)} providers")

    print("\nPhase 2: Generating members & enrollment...")
    members, dependents, eligibility = generate_members(2000, employers, plans)
    assign_pcps(members, providers)
    print(f"  → {len(members)} primary members")
    print(f"  → {len(dependents)} dependents")
    print(f"  → {len(eligibility)} eligibility periods")

    print("\nPhase 3: Generating claims & transactions...")
    medical_claims, claim_lines = generate_medical_claims(members, dependents, providers, plans)
    print(f"  → {len(medical_claims)} medical claims")
    print(f"  → {len(claim_lines)} claim lines")

    rx_claims = generate_pharmacy_claims(members, dependents, plans)
    print(f"  → {len(rx_claims)} pharmacy claims")

    print("\nPhase 4: Generating authorizations & accumulators...")
    auths = generate_authorizations(members, providers, plans)
    print(f"  → {len(auths)} authorizations")

    plan_lookup = {p["plan_id"]: p for p in plans}
    accumulators = generate_accumulators(members, medical_claims, plan_lookup)
    print(f"  → {len(accumulators)} accumulator records")

    # Reference data export
    print("\nPhase 5: Exporting JSON...")
    save_json(employers, "employers.json")
    save_json(plans, "plans.json")
    save_json(benefits, "benefits.json")
    save_json(providers, "providers.json")
    save_json(members, "members.json")
    save_json(dependents, "dependents.json")
    save_json(eligibility, "eligibility.json")
    save_json(medical_claims, "medical_claims.json")
    save_json(claim_lines, "claim_lines.json")
    save_json(rx_claims, "pharmacy_claims.json")
    save_json(auths, "authorizations.json")
    save_json(accumulators, "accumulators.json")
    save_json(DIAGNOSIS_CODES, "reference_diagnosis_codes.json")
    save_json(PROCEDURE_CODES, "reference_procedure_codes.json")
    save_json(MEDICATIONS, "reference_medications.json")
    save_json(PLACE_OF_SERVICE, "reference_place_of_service.json")

    print("\nPhase 6: Exporting CSV...")
    save_csv(employers, "employers.csv")
    save_csv(plans, "plans.csv")
    save_csv(benefits, "benefits.csv")
    save_csv(providers, "providers.csv")
    save_csv(members, "members.csv")
    save_csv(dependents, "dependents.csv")
    save_csv(eligibility, "eligibility.csv")
    save_csv(medical_claims, "medical_claims.csv")
    save_csv(claim_lines, "claim_lines.csv")
    save_csv(rx_claims, "pharmacy_claims.csv")
    save_csv(auths, "authorizations.csv")
    save_csv(accumulators, "accumulators.csv")

    # Generate summary stats
    total_billed = sum(c["total_billed"] for c in medical_claims)
    total_paid = sum(c["total_plan_paid"] for c in medical_claims)
    total_rx = sum(c["total_cost"] for c in rx_claims)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "entity_counts": {
            "employers": len(employers),
            "plans": len(plans),
            "benefits": len(benefits),
            "providers": len(providers),
            "members_primary": len(members),
            "dependents": len(dependents),
            "total_covered_lives": len(members) + len(dependents),
            "eligibility_periods": len(eligibility),
            "medical_claims": len(medical_claims),
            "claim_lines": len(claim_lines),
            "pharmacy_claims": len(rx_claims),
            "authorizations": len(auths),
            "accumulators": len(accumulators),
        },
        "financial_summary": {
            "total_medical_billed": money(total_billed),
            "total_medical_paid": money(total_paid),
            "total_pharmacy_cost": money(total_rx),
            "avg_claim_amount": money(total_billed / len(medical_claims)) if medical_claims else 0,
            "claim_denial_rate": round(sum(1 for c in medical_claims if c["claim_status"] == "Denied") / len(medical_claims) * 100, 1) if medical_claims else 0,
            "auth_approval_rate": round(sum(1 for a in auths if a["status"] == "Approved") / len(auths) * 100, 1) if auths else 0,
        },
    }
    save_json(summary, "summary.json")

    print("\n" + "=" * 60)
    print("Generation Complete!")
    print(f"  Total covered lives: {len(members) + len(dependents):,}")
    print(f"  Total medical claims: {len(medical_claims):,}")
    print(f"  Total pharmacy claims: {len(rx_claims):,}")
    print(f"  Total billed: ${total_billed:,.2f}")
    print(f"  Total plan paid: ${total_paid:,.2f}")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    main()
