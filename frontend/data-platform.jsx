import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  Menu, X, Home, Database, Code, FileText, Share2,
  ChevronDown, ChevronRight, Search, Users, Briefcase, Heart,
  Pill, FileCheck, Shield, TrendingUp
} from 'lucide-react';

const HealthcareDataPlatform = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [expandedEntity, setExpandedEntity] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Entity schema definitions
  const entitySchemas = {
    Employers: {
      icon: Briefcase,
      color: 'blue',
      fields: [
        { name: 'employer_id', type: 'UUID', description: 'Unique employer identifier' },
        { name: 'name', type: 'String', description: 'Legal employer name' },
        { name: 'tax_id', type: 'String', description: 'EIN/Tax identifier' },
        { name: 'industry', type: 'String', description: 'Industry classification' },
        { name: 'size_category', type: 'Enum', description: 'Small/Medium/Large/Enterprise' },
        { name: 'employee_count', type: 'Integer', description: 'Current employee count' },
        { name: 'address', type: 'Object', description: 'Business address (line1/line2/city/state/zip)' },
        { name: 'phone', type: 'String', description: 'Contact phone number' },
        { name: 'effective_date', type: 'Date', description: 'Contract effective date' },
        { name: 'status', type: 'Enum', description: 'Active/Inactive/Pending' },
        { name: 'account_manager', type: 'String', description: 'Account manager name' }
      ]
    },
    Plans: {
      icon: Heart,
      color: 'teal',
      fields: [
        { name: 'plan_id', type: 'UUID', description: 'Unique plan identifier' },
        { name: 'employer_id', type: 'UUID (FK)', description: 'Reference to employer' },
        { name: 'plan_name', type: 'String', description: 'Plan name/description' },
        { name: 'plan_type', type: 'Enum', description: 'HMO/PPO/EPO/HDHP/POS' },
        { name: 'tier', type: 'Enum', description: 'Bronze/Silver/Gold/Platinum' },
        { name: 'effective_date', type: 'Date', description: 'Plan effective date' },
        { name: 'termination_date', type: 'Date', description: 'Plan termination date (if any)' },
        { name: 'status', type: 'Enum', description: 'Active/Inactive' },
        { name: 'deductible_individual', type: 'Decimal', description: 'Individual deductible amount' },
        { name: 'deductible_family', type: 'Decimal', description: 'Family deductible amount' },
        { name: 'out_of_pocket_max_individual', type: 'Decimal', description: 'Individual OOP max' },
        { name: 'out_of_pocket_max_family', type: 'Decimal', description: 'Family OOP max' },
        { name: 'monthly_premium_individual', type: 'Decimal', description: 'Individual monthly premium' },
        { name: 'monthly_premium_family', type: 'Decimal', description: 'Family monthly premium' },
        { name: 'coinsurance_in_network', type: 'Integer', description: 'In-network coinsurance percent' },
        { name: 'coinsurance_out_of_network', type: 'Integer', description: 'Out-of-network coinsurance percent' },
        { name: 'copay_pcp', type: 'Decimal', description: 'Primary care copay' },
        { name: 'copay_specialist', type: 'Decimal', description: 'Specialist copay' },
        { name: 'copay_er', type: 'Decimal', description: 'Emergency room copay' },
        { name: 'copay_urgent_care', type: 'Decimal', description: 'Urgent care copay' },
        { name: 'copay_rx_generic', type: 'Decimal', description: 'Generic Rx copay' },
        { name: 'copay_rx_preferred_brand', type: 'Decimal', description: 'Preferred brand Rx copay' },
        { name: 'copay_rx_non_preferred', type: 'Decimal', description: 'Non-preferred brand Rx copay' },
        { name: 'copay_rx_specialty', type: 'Decimal', description: 'Specialty Rx copay' },
        { name: 'network_name', type: 'String', description: 'Network provider name' },
        { name: 'pharmacy_benefit_manager', type: 'String', description: 'PBM name' }
      ]
    },
    Benefits: {
      icon: Shield,
      color: 'cyan',
      fields: [
        { name: 'benefit_id', type: 'UUID', description: 'Unique benefit identifier' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'category', type: 'String', description: 'Service category (e.g., Primary Care Visit, Imaging)' },
        { name: 'network_tier', type: 'Enum', description: 'In-Network/Out-of-Network' },
        { name: 'cost_sharing_type', type: 'String', description: 'Copay/Coinsurance/Deductible' },
        { name: 'deductible_applies', type: 'String', description: 'Deductible applicability text' },
        { name: 'description', type: 'String', description: 'Benefit description' },
        { name: 'annual_limit', type: 'Decimal', description: 'Annual benefit limit (if any)' },
        { name: 'requires_auth', type: 'Boolean', description: 'Prior auth required flag' },
        { name: 'requires_referral', type: 'Boolean', description: 'Referral required flag' }
      ]
    },
    Providers: {
      icon: Users,
      color: 'indigo',
      fields: [
        { name: 'provider_id', type: 'UUID', description: 'Unique provider identifier' },
        { name: 'npi', type: 'String', description: 'National Provider Identifier' },
        { name: 'name', type: 'String', description: 'Provider name' },
        { name: 'type', type: 'Enum', description: 'Individual/Facility' },
        { name: 'specialty', type: 'String', description: 'Medical specialty' },
        { name: 'tax_id', type: 'String', description: 'Tax ID/SSN' },
        { name: 'address', type: 'Object', description: 'Practice address (line1/line2/city/state/zip)' },
        { name: 'phone', type: 'String', description: 'Contact phone' },
        { name: 'accepting_new_patients', type: 'Boolean', description: 'Accepting patients flag' },
        { name: 'network_status', type: 'Enum', description: 'In-Network/Out-of-Network/Pending' },
        { name: 'languages', type: 'Array[String]', description: 'Languages spoken' },
        { name: 'rating', type: 'Decimal', description: 'Average rating score' },
        { name: 'effective_date', type: 'Date', description: 'Network effective date' }
      ]
    },
    Members: {
      icon: Users,
      color: 'purple',
      fields: [
        { name: 'member_id', type: 'UUID', description: 'Unique member identifier' },
        { name: 'subscriber_id', type: 'String', description: 'Subscriber/primary member reference' },
        { name: 'employer_id', type: 'UUID (FK)', description: 'Reference to employer' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'first_name', type: 'String', description: 'Member first name' },
        { name: 'last_name', type: 'String', description: 'Member last name' },
        { name: 'date_of_birth', type: 'Date', description: 'Member DOB' },
        { name: 'age', type: 'Integer', description: 'Current age' },
        { name: 'gender', type: 'Enum', description: 'M/F' },
        { name: 'ssn_last4', type: 'String', description: 'Last 4 SSN digits' },
        { name: 'email', type: 'String', description: 'Email address' },
        { name: 'phone', type: 'String', description: 'Phone number' },
        { name: 'address', type: 'Object', description: 'Mailing address (line1/line2/city/state/zip)' },
        { name: 'coverage_type', type: 'Enum', description: 'Employee/Dependent' },
        { name: 'relationship', type: 'String', description: 'Self/Spouse/Child' },
        { name: 'pcp_provider_id', type: 'UUID (FK)', description: 'Primary care physician' },
        { name: 'status', type: 'Enum', description: 'Active/Terminated' },
        { name: 'enrollment_date', type: 'Date', description: 'Coverage start date' },
        { name: 'termination_date', type: 'Date', description: 'Coverage end date' },
        { name: 'chronic_conditions', type: 'Array[String]', description: 'Chronic conditions list' }
      ]
    },
    Dependents: {
      icon: Users,
      color: 'pink',
      fields: [
        { name: 'member_id', type: 'UUID', description: 'Dependent member identifier' },
        { name: 'subscriber_id', type: 'UUID', description: 'Primary subscriber reference' },
        { name: 'subscriber_member_id', type: 'UUID (FK)', description: 'FK to primary member' },
        { name: 'employer_id', type: 'UUID (FK)', description: 'Reference to employer' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'first_name', type: 'String', description: 'Dependent first name' },
        { name: 'last_name', type: 'String', description: 'Dependent last name' },
        { name: 'date_of_birth', type: 'Date', description: 'Dependent DOB' },
        { name: 'gender', type: 'Enum', description: 'M/F/Other' },
        { name: 'relationship', type: 'Enum', description: 'Spouse/Child/Parent' },
        { name: 'status', type: 'Enum', description: 'Active/Terminated' },
        { name: 'enrollment_date', type: 'Date', description: 'Coverage start date' }
      ]
    },
    Eligibility: {
      icon: FileCheck,
      color: 'green',
      fields: [
        { name: 'eligibility_id', type: 'UUID', description: 'Unique eligibility record ID' },
        { name: 'member_id', type: 'UUID (FK)', description: 'Reference to member' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'coverage_type', type: 'Enum', description: 'Medical/Dental/Vision/Behavioral' },
        { name: 'effective_date', type: 'Date', description: 'Coverage effective date' },
        { name: 'termination_date', type: 'Date', description: 'Coverage termination date' },
        { name: 'status', type: 'Enum', description: 'Active/Terminated/Suspended' },
        { name: 'cobra_flag', type: 'Boolean', description: 'COBRA continuation flag' }
      ]
    },
    'Medical Claims': {
      icon: FileCheck,
      color: 'orange',
      fields: [
        { name: 'claim_id', type: 'UUID', description: 'Unique claim identifier' },
        { name: 'member_id', type: 'UUID (FK)', description: 'Reference to member' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'provider_id', type: 'UUID (FK)', description: 'Reference to provider' },
        { name: 'claim_type', type: 'Enum', description: 'Professional/Institutional' },
        { name: 'claim_status', type: 'Enum', description: 'Paid/Denied/Pending/Adjusted/Appealed' },
        { name: 'service_date', type: 'Date', description: 'Date service provided' },
        { name: 'received_date', type: 'Date', description: 'Claim received date' },
        { name: 'processed_date', type: 'Date', description: 'Claim processed date' },
        { name: 'primary_diagnosis', type: 'String', description: 'Primary ICD-10 diagnosis' },
        { name: 'primary_diagnosis_description', type: 'String', description: 'Primary diagnosis description' },
        { name: 'secondary_diagnosis', type: 'String', description: 'Secondary ICD-10 diagnosis' },
        { name: 'place_of_service', type: 'String', description: 'Place of service code' },
        { name: 'place_of_service_description', type: 'String', description: 'Place of service description' },
        { name: 'total_billed', type: 'Decimal', description: 'Total billed amount' },
        { name: 'total_allowed', type: 'Decimal', description: 'Total allowed amount' },
        { name: 'total_plan_paid', type: 'Decimal', description: 'Amount plan paid' },
        { name: 'total_member_responsibility', type: 'Decimal', description: 'Member coinsurance/copay' },
        { name: 'denial_reason', type: 'String', description: 'Reason for denial if applicable' },
        { name: 'appeal_status', type: 'Enum', description: 'Appealed/Not Appealed/Overturned' },
        { name: 'check_number', type: 'String', description: 'Payment check number' },
        { name: 'payment_date', type: 'Date', description: 'Payment date' }
      ]
    },
    'Claim Lines': {
      icon: TrendingUp,
      color: 'red',
      fields: [
        { name: 'claim_line_id', type: 'UUID', description: 'Unique claim line identifier' },
        { name: 'claim_id', type: 'UUID (FK)', description: 'Reference to medical claim' },
        { name: 'line_number', type: 'Integer', description: 'Line sequence number' },
        { name: 'procedure_code', type: 'String', description: 'CPT/HCPCS procedure code' },
        { name: 'procedure_description', type: 'String', description: 'Procedure description' },
        { name: 'modifier', type: 'String', description: 'Procedure modifier code' },
        { name: 'units', type: 'Decimal', description: 'Number of units' },
        { name: 'diagnosis_pointer', type: 'Integer', description: 'Primary diagnosis reference' },
        { name: 'billed_amount', type: 'Decimal', description: 'Provider billed amount' },
        { name: 'allowed_amount', type: 'Decimal', description: 'Plan allowed amount' },
        { name: 'plan_paid_amount', type: 'Decimal', description: 'Amount plan paid' },
        { name: 'member_responsibility', type: 'Decimal', description: 'Member responsibility' },
        { name: 'service_date', type: 'Date', description: 'Service date' }
      ]
    },
    'Pharmacy Claims': {
      icon: Pill,
      color: 'emerald',
      fields: [
        { name: 'rx_claim_id', type: 'UUID', description: 'Unique pharmacy claim ID' },
        { name: 'member_id', type: 'UUID (FK)', description: 'Reference to member' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'fill_date', type: 'Date', description: 'Prescription fill date' },
        { name: 'medication_name', type: 'String', description: 'Drug name' },
        { name: 'ndc', type: 'String', description: 'National Drug Code' },
        { name: 'medication_category', type: 'String', description: 'Drug category' },
        { name: 'quantity', type: 'Integer', description: 'Quantity dispensed' },
        { name: 'days_supply', type: 'Integer', description: 'Days of supply' },
        { name: 'refill_number', type: 'Integer', description: 'Refill number' },
        { name: 'prescriber_npi', type: 'String', description: 'Prescriber NPI' },
        { name: 'pharmacy_npi', type: 'String', description: 'Pharmacy NPI' },
        { name: 'pharmacy_name', type: 'String', description: 'Pharmacy name' },
        { name: 'formulary_status', type: 'Enum', description: 'Preferred/Non-Preferred/Specialty' },
        { name: 'prior_auth_required', type: 'Boolean', description: 'Prior authorization required' },
        { name: 'ingredient_cost', type: 'Decimal', description: 'Drug ingredient cost' },
        { name: 'dispensing_fee', type: 'Decimal', description: 'Pharmacy dispensing fee' },
        { name: 'total_cost', type: 'Decimal', description: 'Total drug cost' },
        { name: 'member_copay', type: 'Decimal', description: 'Member copay amount' },
        { name: 'plan_paid', type: 'Decimal', description: 'Amount plan paid' },
        { name: 'claim_status', type: 'Enum', description: 'Paid/Denied/Pending' },
        { name: 'daw_code', type: 'String', description: 'Dispense as Written code' }
      ]
    },
    Authorizations: {
      icon: Shield,
      color: 'amber',
      fields: [
        { name: 'auth_id', type: 'UUID', description: 'Unique authorization ID' },
        { name: 'member_id', type: 'UUID (FK)', description: 'Reference to member' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'provider_id', type: 'UUID (FK)', description: 'Reference to provider' },
        { name: 'auth_type', type: 'Enum', description: 'Prior Authorization' },
        { name: 'service_description', type: 'String', description: 'Service being authorized' },
        { name: 'procedure_code', type: 'String', description: 'CPT code for service' },
        { name: 'service_category', type: 'String', description: 'Surgery/Imaging/Behavioral' },
        { name: 'status', type: 'Enum', description: 'Approved/Denied/Pending' },
        { name: 'request_date', type: 'Date', description: 'Authorization request date' },
        { name: 'decision_date', type: 'Date', description: 'Decision date' },
        { name: 'effective_date', type: 'Date', description: 'Authorization effective date' },
        { name: 'expiration_date', type: 'Date', description: 'Authorization expiration date' },
        { name: 'approved_units', type: 'Integer', description: 'Units approved' },
        { name: 'requested_units', type: 'Integer', description: 'Units requested' },
        { name: 'denial_reason', type: 'String', description: 'Denial reason if applicable' },
        { name: 'clinical_notes', type: 'String', description: 'Clinical reviewer notes' },
        { name: 'urgency', type: 'Enum', description: 'Standard/Urgent/Emergency' },
        { name: 'reviewer', type: 'String', description: 'Reviewer name/ID' }
      ]
    },
    Accumulators: {
      icon: TrendingUp,
      color: 'lime',
      fields: [
        { name: 'accumulator_id', type: 'UUID', description: 'Unique accumulator record ID' },
        { name: 'member_id', type: 'UUID (FK)', description: 'Reference to member' },
        { name: 'plan_id', type: 'UUID (FK)', description: 'Reference to plan' },
        { name: 'plan_year', type: 'Integer', description: 'Plan year' },
        { name: 'deductible_limit', type: 'Decimal', description: 'Annual deductible limit' },
        { name: 'deductible_used', type: 'Decimal', description: 'Deductible amount used' },
        { name: 'deductible_remaining', type: 'Decimal', description: 'Deductible remaining' },
        { name: 'oop_max_limit', type: 'Decimal', description: 'Annual OOP maximum' },
        { name: 'oop_used', type: 'Decimal', description: 'OOP amount used' },
        { name: 'oop_remaining', type: 'Decimal', description: 'OOP amount remaining' },
        { name: 'last_updated', type: 'DateTime', description: 'Last update timestamp' }
      ]
    }
  };

  // Summary metrics
  const metrics = [
    { label: 'Employers', value: '25', icon: Briefcase, color: 'blue' },
    { label: 'Benefit Plans', value: '50', icon: Heart, color: 'teal' },
    { label: 'Benefit Line Items', value: '900', icon: Shield, color: 'cyan' },
    { label: 'Providers', value: '300', icon: Users, color: 'indigo' },
    { label: 'Primary Members', value: '2,000', icon: Users, color: 'purple' },
    { label: 'Dependents', value: '2,297', icon: Users, color: 'pink' },
    { label: 'Total Covered Lives', value: '4,297', icon: TrendingUp, color: 'green' },
    { label: 'Eligibility Periods', value: '4,297', icon: FileCheck, color: 'emerald' }
  ];

  const claimMetrics = [
    { label: 'Medical Claims', value: '13,841', icon: FileCheck, color: 'orange' },
    { label: 'Claim Lines', value: '24,206', icon: TrendingUp, color: 'red' },
    { label: 'Pharmacy Claims', value: '7,055', icon: Pill, color: 'emerald' },
    { label: 'Authorizations', value: '567', icon: Shield, color: 'amber' },
    { label: 'Accumulator Records', value: '2,000', icon: TrendingUp, color: 'lime' }
  ];

  const financialMetrics = [
    { label: 'Total Medical Billed', value: '$63,278,604.76' },
    { label: 'Total Medical Paid', value: '$33,998,600.33' },
    { label: 'Claim Denial Rate', value: '~8%' },
    { label: 'Auth Approval Rate', value: '~55%' }
  ];

  // Sample API payloads
  const apiExamples = {
    member: {
      endpoint: 'GET /api/members/:id',
      description: 'Retrieve member details',
      payload: {
        member_id: '550e8400-e29b-41d4-a716-446655440000',
        subscriber_id: '550e8400-e29b-41d4-a716-446655440000',
        employer_id: '550e8400-e29b-41d4-a716-446655440001',
        plan_id: '550e8400-e29b-41d4-a716-446655440002',
        first_name: 'John',
        last_name: 'Smith',
        date_of_birth: '1985-03-15',
        age: 39,
        gender: 'M',
        email: 'john.smith@email.com',
        coverage_type: 'Employee',
        status: 'Active',
        enrollment_date: '2023-01-01',
        chronic_conditions: ['Diabetes Type 2', 'Hypertension']
      }
    },
    claims: {
      endpoint: 'GET /api/members/:id/claims',
      description: 'Retrieve claims for a member',
      payload: {
        claims: [
          {
            claim_id: '550e8400-e29b-41d4-a716-446655440010',
            member_id: '550e8400-e29b-41d4-a716-446655440000',
            claim_status: 'Paid',
            service_date: '2024-01-15',
            total_billed: 5000.00,
            total_allowed: 3500.00,
            total_plan_paid: 2800.00,
            total_member_responsibility: 700.00
          }
        ],
        total_count: 42,
        paid_count: 39,
        denied_count: 3
      }
    },
    deniedClaims: {
      endpoint: 'GET /api/claims?status=Denied',
      description: 'Retrieve denied claims',
      payload: {
        claims: [
          {
            claim_id: '550e8400-e29b-41d4-a716-446655440020',
            member_id: '550e8400-e29b-41d4-a716-446655440000',
            claim_status: 'Denied',
            denial_reason: 'Non-covered service',
            total_billed: 2000.00
          }
        ],
        total_denied: 1107
      }
    },
    authorization: {
      endpoint: 'GET /api/authorizations/:id',
      description: 'Retrieve authorization details',
      payload: {
        auth_id: '550e8400-e29b-41d4-a716-446655440030',
        member_id: '550e8400-e29b-41d4-a716-446655440000',
        service_description: 'MRI Brain without contrast',
        procedure_code: '70553',
        status: 'Approved',
        request_date: '2024-01-10',
        decision_date: '2024-01-10',
        approved_units: 1,
        effective_date: '2024-01-11',
        expiration_date: '2024-04-10'
      }
    }
  };

  // File manifest data
  const fileManifest = [
    { name: 'employers.json', records: '25', description: 'All employers with metadata' },
    { name: 'employers.csv', records: '25', description: 'Employers CSV export' },
    { name: 'plans.json', records: '50', description: 'Benefit plans with full configuration' },
    { name: 'plans.csv', records: '50', description: 'Plans CSV export' },
    { name: 'benefits.json', records: '900', description: 'Benefit line items' },
    { name: 'benefits.csv', records: '900', description: 'Benefits CSV export' },
    { name: 'providers.json', records: '300', description: 'Healthcare providers' },
    { name: 'providers.csv', records: '300', description: 'Providers CSV export' },
    { name: 'members.json', records: '2,000', description: 'Primary members and employees' },
    { name: 'members.csv', records: '2,000', description: 'Members CSV export' },
    { name: 'dependents.json', records: '2,297', description: 'Dependent family members' },
    { name: 'dependents.csv', records: '2,297', description: 'Dependents CSV export' },
    { name: 'eligibility.json', records: '4,297', description: 'Coverage eligibility periods' },
    { name: 'eligibility.csv', records: '4,297', description: 'Eligibility CSV export' },
    { name: 'medical_claims.json', records: '13,841', description: 'Medical claim headers' },
    { name: 'medical_claims.csv', records: '13,841', description: 'Medical claims CSV export' },
    { name: 'claim_lines.json', records: '24,206', description: 'Medical claim detail lines' },
    { name: 'claim_lines.csv', records: '24,206', description: 'Claim lines CSV export' },
    { name: 'pharmacy_claims.json', records: '7,055', description: 'Pharmacy claims' },
    { name: 'pharmacy_claims.csv', records: '7,055', description: 'Pharmacy claims CSV export' },
    { name: 'authorizations.json', records: '567', description: 'Prior authorization records' },
    { name: 'authorizations.csv', records: '567', description: 'Authorizations CSV export' },
    { name: 'accumulators.json', records: '2,000', description: 'Deductible and OOP tracking' },
    { name: 'accumulators.csv', records: '2,000', description: 'Accumulators CSV export' }
  ];

  // Dashboard data
  const entityCountData = [
    { name: 'Employers', value: 25 },
    { name: 'Plans', value: 50 },
    { name: 'Providers', value: 300 },
    { name: 'Members', value: 2000 },
    { name: 'Dependents', value: 2297 }
  ];

  const claimStatusData = [
    { name: 'Paid', value: 12883, color: '#10b981' },
    { name: 'Denied', value: 1107, color: '#ef4444' },
    { name: 'Pending', value: 564, color: '#f59e0b' },
    { name: 'Appeal', value: 287, color: '#3b82f6' }
  ];

  // Filter entities based on search
  const filteredEntities = useMemo(() => {
    if (!searchTerm) return Object.keys(entitySchemas);
    return Object.keys(entitySchemas).filter(entity =>
      entity.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm]);

  const colorMap = {
    blue: 'bg-blue-50 border-blue-200',
    teal: 'bg-teal-50 border-teal-200',
    cyan: 'bg-cyan-50 border-cyan-200',
    indigo: 'bg-indigo-50 border-indigo-200',
    purple: 'bg-purple-50 border-purple-200',
    pink: 'bg-pink-50 border-pink-200',
    green: 'bg-green-50 border-green-200',
    emerald: 'bg-emerald-50 border-emerald-200',
    orange: 'bg-orange-50 border-orange-200',
    red: 'bg-red-50 border-red-200',
    amber: 'bg-amber-50 border-amber-200',
    lime: 'bg-lime-50 border-lime-200'
  };

  const colorBadge = {
    blue: 'bg-blue-100 text-blue-800',
    teal: 'bg-teal-100 text-teal-800',
    cyan: 'bg-cyan-100 text-cyan-800',
    indigo: 'bg-indigo-100 text-indigo-800',
    purple: 'bg-purple-100 text-purple-800',
    pink: 'bg-pink-100 text-pink-800',
    green: 'bg-green-100 text-green-800',
    emerald: 'bg-emerald-100 text-emerald-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
    amber: 'bg-amber-100 text-amber-800',
    lime: 'bg-lime-100 text-lime-800'
  };

  // Sidebar navigation
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'explorer', label: 'Data Model', icon: Database },
    { id: 'api', label: 'API Reference', icon: Code },
    { id: 'files', label: 'File Manifest', icon: FileText },
    { id: 'erd', label: 'Entity Diagram', icon: Share2 }
  ];

  // Render functions for each section
  const renderDashboard = () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Dataset Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <div
                key={idx}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-600 text-sm font-medium">{metric.label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{metric.value}</p>
                  </div>
                  <Icon className="w-8 h-8 text-gray-400" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Claims & Authorizations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {claimMetrics.map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <div
                key={idx}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-600 text-sm font-medium">{metric.label}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2">{metric.value}</p>
                  </div>
                  <Icon className="w-6 h-6 text-gray-400" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className="text-2xl font-bold text-gray-900 mb-6">Financial Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {financialMetrics.map((metric, idx) => (
            <div
              key={idx}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
            >
              <p className="text-gray-600 text-sm font-medium">{metric.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">{metric.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Entity Counts</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={entityCountData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0891b2" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Medical Claim Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={claimStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {claimStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  const renderExplorer = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Data Model Explorer</h2>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search entities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
        </div>

        {filteredEntities.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No entities found matching your search.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredEntities.map((entityName) => {
              const schema = entitySchemas[entityName];
              const Icon = schema.icon;
              const isExpanded = expandedEntity === entityName;

              return (
                <div
                  key={entityName}
                  className={`border rounded-lg transition-all duration-200 ${
                    colorMap[schema.color]
                  } ${isExpanded ? 'col-span-1 md:col-span-2' : ''}`}
                >
                  <button
                    onClick={() =>
                      setExpandedEntity(isExpanded ? null : entityName)
                    }
                    className="w-full text-left p-4 flex items-center justify-between hover:bg-opacity-75 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-6 h-6 text-gray-700" />
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {entityName}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {schema.fields.length} fields
                        </p>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-700" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-700" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="border-t px-4 py-4 bg-opacity-50">
                      <div className="space-y-3">
                        {schema.fields.map((field, idx) => (
                          <div
                            key={idx}
                            className="bg-white bg-opacity-50 rounded p-3 border border-gray-200"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1">
                                <p className="font-mono text-sm font-semibold text-gray-900">
                                  {field.name}
                                </p>
                                <p className="text-xs text-gray-600 mt-1">
                                  {field.description}
                                </p>
                              </div>
                              <span
                                className={`text-xs font-semibold px-2 py-1 rounded whitespace-nowrap ${
                                  colorBadge[schema.color]
                                }`}
                              >
                                {field.type}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );

  const renderAPI = () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">API Reference</h2>
        <p className="text-gray-600 mb-8">
          Example endpoints and JSON payloads for integrating with the healthcare data platform.
        </p>

        {Object.entries(apiExamples).map((item) => {
          const [key, example] = item;
          return (
            <div
              key={key}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
            >
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 font-mono">
                  {example.endpoint}
                </h3>
                <p className="text-gray-600 text-sm mt-2">
                  {example.description}
                </p>
              </div>

              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-auto">
                <pre className="text-gray-100">
                  {JSON.stringify(example.payload, null, 2)}
                </pre>
              </div>
            </div>
          );
        })}

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-semibold text-blue-900 mb-2">Common Query Patterns</h4>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="font-mono font-semibold">GET /api/members</span>
              - List all members with pagination
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono font-semibold">
                GET /api/members/:id/claims
              </span>
              - Member's claims history
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono font-semibold">
                GET /api/claims?status=Denied
              </span>
              - Filter claims by status
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono font-semibold">
                GET /api/authorizations/:id
              </span>
              - Authorization details
            </li>
            <li className="flex items-start gap-2">
              <span className="font-mono font-semibold">
                GET /api/members/:id/accumulators
              </span>
              - Deductible and OOP status
            </li>
          </ul>
        </div>
      </div>
    </div>
  );

  const renderFiles = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">File Manifest</h2>
        <p className="text-gray-600 mb-6">
          Complete listing of all JSON and CSV files in the dataset.
        </p>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-6 py-3 font-semibold text-gray-900">
                    Filename
                  </th>
                  <th className="text-left px-6 py-3 font-semibold text-gray-900">
                    Record Count
                  </th>
                  <th className="text-left px-6 py-3 font-semibold text-gray-900">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {fileManifest.map((file, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 font-mono text-sm text-gray-900">
                      {file.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {file.records}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {file.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  const renderERD = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Entity Relationship Diagram</h2>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 overflow-auto">
          <svg viewBox="0 0 1400 900" className="w-full min-h-[600px]">
            {/* Define relationship lines */}
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#9ca3af" />
              </marker>
            </defs>

            {/* Relationship lines */}
            <line
              x1="150"
              y1="100"
              x2="150"
              y2="200"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="150"
              y1="100"
              x2="350"
              y2="200"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="350"
              y1="100"
              x2="550"
              y2="200"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="750"
              y1="100"
              x2="750"
              y2="200"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="150"
              y1="300"
              x2="150"
              y2="400"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="350"
              y1="300"
              x2="350"
              y2="400"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="550"
              y1="300"
              x2="550"
              y2="400"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="750"
              y1="300"
              x2="900"
              y2="400"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="900"
              y1="300"
              x2="1050"
              y2="400"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="150"
              y1="500"
              x2="350"
              y2="600"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="350"
              y1="500"
              x2="550"
              y2="600"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="550"
              y1="500"
              x2="750"
              y2="600"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
            <line
              x1="750"
              y1="500"
              x2="900"
              y2="600"
              stroke="#d1d5db"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />

            {/* Entity boxes - Level 0 */}
            <rect
              x="100"
              y="50"
              width="100"
              height="50"
              fill="#dbeafe"
              stroke="#0284c7"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="150"
              y="82"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#0c4a6e"
            >
              Employers
            </text>

            <rect
              x="300"
              y="50"
              width="100"
              height="50"
              fill="#ccfbf1"
              stroke="#0d9488"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="350"
              y="82"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#134e4a"
            >
              Plans
            </text>

            <rect
              x="500"
              y="50"
              width="100"
              height="50"
              fill="#cffafe"
              stroke="#0891b2"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="550"
              y="82"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#164e63"
            >
              Benefits
            </text>

            <rect
              x="700"
              y="50"
              width="100"
              height="50"
              fill="#e0e7ff"
              stroke="#4f46e5"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="750"
              y="82"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#312e81"
            >
              Providers
            </text>

            {/* Entity boxes - Level 1 */}
            <rect
              x="100"
              y="200"
              width="100"
              height="50"
              fill="#f3e8ff"
              stroke="#a855f7"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="150"
              y="232"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#581c87"
            >
              Members
            </text>

            <rect
              x="300"
              y="200"
              width="100"
              height="50"
              fill="#fce7f3"
              stroke="#ec4899"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="350"
              y="232"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#831843"
            >
              Dependents
            </text>

            <rect
              x="500"
              y="200"
              width="100"
              height="50"
              fill="#dcfce7"
              stroke="#22c55e"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="550"
              y="232"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#15803d"
            >
              Eligibility
            </text>

            <rect
              x="700"
              y="200"
              width="100"
              height="50"
              fill="#fed7aa"
              stroke="#f97316"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="750"
              y="232"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#7c2d12"
            >
              Auth Request
            </text>

            <rect
              x="900"
              y="200"
              width="100"
              height="50"
              fill="#fecaca"
              stroke="#ef4444"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="950"
              y="232"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#7f1d1d"
            >
              Med Claims
            </text>

            {/* Entity boxes - Level 2 */}
            <rect
              x="100"
              y="400"
              width="100"
              height="50"
              fill="#fef3c7"
              stroke="#eab308"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="150"
              y="432"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#713f12"
            >
              Claim Lines
            </text>

            <rect
              x="300"
              y="400"
              width="100"
              height="50"
              fill="#d1fae5"
              stroke="#10b981"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="350"
              y="432"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#065f46"
            >
              Pharmacy
            </text>

            <rect
              x="500"
              y="400"
              width="100"
              height="50"
              fill="#f0fdf4"
              stroke="#84cc16"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="550"
              y="432"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#355e3b"
            >
              Accumulators
            </text>

            <rect
              x="750"
              y="400"
              width="100"
              height="50"
              fill="#fdf2f8"
              stroke="#db2777"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="800"
              y="432"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#500724"
            >
              Authorizations
            </text>

            <rect
              x="1000"
              y="400"
              width="100"
              height="50"
              fill="#e0f2fe"
              stroke="#0284c7"
              strokeWidth="2"
              rx="4"
            />
            <text
              x="1050"
              y="432"
              textAnchor="middle"
              className="font-semibold"
              fontSize="12"
              fill="#0c4a6e"
            >
              Claims (Rx)
            </text>

            {/* Legend */}
            <text
              x="50"
              y="800"
              fontSize="14"
              fontWeight="bold"
              fill="#1f2937"
            >
              Entity Relationships:
            </text>
            <text
              x="50"
              y="830"
              fontSize="12"
              fill="#6b7280"
            >
              → Foreign Key (1:N relationship)
            </text>
            <text
              x="50"
              y="860"
              fontSize="12"
              fill="#6b7280"
            >
              Arrows point from parent to child entities
            </text>
          </svg>
        </div>

        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-6">
          <h4 className="font-semibold text-amber-900 mb-3">Key Relationships</h4>
          <ul className="space-y-2 text-sm text-amber-800">
            <li>
              <span className="font-semibold">Employers → Plans</span>: One employer has multiple plans
            </li>
            <li>
              <span className="font-semibold">Plans → Benefits</span>: Each plan has multiple benefits
            </li>
            <li>
              <span className="font-semibold">Employers → Members/Dependents</span>: Employer has employees and their families
            </li>
            <li>
              <span className="font-semibold">Members → Eligibility</span>: Member coverage periods tracked separately
            </li>
            <li>
              <span className="font-semibold">Members → Claims</span>: Multiple medical and pharmacy claims per member
            </li>
            <li>
              <span className="font-semibold">Medical Claims → Claim Lines</span>: Claim header with multiple line items
            </li>
            <li>
              <span className="font-semibold">Members → Authorizations</span>: Prior auth requests and decisions
            </li>
            <li>
              <span className="font-semibold">Members → Accumulators</span>: Tracks deductible/OOP per plan year
            </li>
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-gray-900 text-white transition-all duration-300 flex flex-col border-r border-gray-800`}
      >
        <div className="p-4 flex items-center justify-between border-b border-gray-800">
          {sidebarOpen && (
            <h1 className="text-lg font-bold">Healthcare Data</h1>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-800 rounded-lg transition-colors"
          >
            {sidebarOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveSection(item.id);
                  setSearchTerm('');
                  setExpandedEntity(null);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === item.id
                    ? 'bg-cyan-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {sidebarOpen && (
          <div className="p-4 border-t border-gray-800 text-xs text-gray-400">
            <p className="mb-2 font-semibold">Dataset Stats</p>
            <p>4,297 Members</p>
            <p>13,841 Medical Claims</p>
            <p>7,055 Pharmacy Claims</p>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-8 py-6 shadow-sm">
          <h1 className="text-3xl font-bold text-gray-900">
            {navItems.find((item) => item.id === activeSection)?.label}
          </h1>
          <p className="text-gray-600 text-sm mt-1">
            {activeSection === 'dashboard' &&
              'Key metrics and overview of the healthcare synthetic dataset'}
            {activeSection === 'explorer' &&
              'Interactive exploration of all data entities and their fields'}
            {activeSection === 'api' &&
              'Sample endpoints and JSON payloads for integration'}
            {activeSection === 'files' &&
              'Complete inventory of all data files in the dataset'}
            {activeSection === 'erd' &&
              'Visual diagram showing entity relationships and data flow'}
          </p>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-8">
            {activeSection === 'dashboard' && renderDashboard()}
            {activeSection === 'explorer' && renderExplorer()}
            {activeSection === 'api' && renderAPI()}
            {activeSection === 'files' && renderFiles()}
            {activeSection === 'erd' && renderERD()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthcareDataPlatform;
