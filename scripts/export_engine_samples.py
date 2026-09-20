#!/usr/bin/env python3
"""Export real engine-generated sequences and subjects for Jev evaluation."""

import json
from pathlib import Path
from lead_personalization.offer_pack import load_offer_pack
from lead_personalization.copywriter import generate_sequence

pack = load_offer_pack("aevora")

TEST_CASES = [
    {
        "id": "home_design_person_site_video",
        "segment": "home_design",
        "tier": "person",
        "row": {
            "primary_email": "alex@interiordesign.com",
            "first_name": "Alex",
            "last_name": "Rivera",
            "outreach_tier": "person",
            "aevora_segment": "home_design",
            "First_category": "Interior Design",
            "City": "Austin",
            "State": "TX",
        },
        "research": {
            "evidence": "site_video",
            "snippet": "portfolio showcase",
            "research_signal": "embedded video on portfolio page",
            "signal_strength": "strong",
        },
    },
    {
        "id": "creative_marketing_person_linkedin",
        "segment": "creative_marketing",
        "tier": "person",
        "row": {
            "primary_email": "sarah@growthagency.io",
            "first_name": "Sarah",
            "last_name": "Jenkins",
            "outreach_tier": "person",
            "aevora_segment": "creative_marketing",
            "First_category": "Advertising Agency",
            "City": "New York",
            "State": "NY",
        },
        "research": {
            "evidence": "linkedin_posts",
            "snippet": "scaling paid retention in Q4",
            "linkedin_topic": "scaling paid retention in Q4",
            "research_signal": 'recent LinkedIn post: "scaling paid retention in Q4"',
            "signal_strength": "strong",
        },
    },
    {
        "id": "real_estate_company_social_video",
        "segment": "real_estate",
        "tier": "company",
        "row": {
            "primary_email": "info@miamiprimeestates.com",
            "company_name": "Miami Prime Estates",
            "first_name": "",
            "last_name": "",
            "outreach_tier": "company",
            "aevora_segment": "real_estate",
            "First_category": "Commercial Real Estate",
            "City": "Miami",
            "State": "FL",
        },
        "research": {
            "evidence": "social_video",
            "social_channel": "Instagram",
            "snippet": "active Instagram video tour presence",
            "research_signal": "active Instagram account linked from site footer",
            "signal_strength": "strong",
        },
    },
    {
        "id": "software_tech_person_positioning",
        "segment": "software_tech",
        "tier": "person",
        "row": {
            "primary_email": "marcus@devopsflow.io",
            "first_name": "Marcus",
            "last_name": "Vance",
            "outreach_tier": "person",
            "aevora_segment": "software_tech",
            "First_category": "Software Company",
            "City": "San Francisco",
            "State": "CA",
        },
        "research": {
            "evidence": "positioning",
            "snippet": "fastest CI/CD observability for Kubernetes",
            "research_signal": 'site positioning: "fastest CI/CD observability for Kubernetes"',
            "signal_strength": "strong",
        },
    },
    {
        "id": "medical_aesthetic_company_weak",
        "segment": "medical_aesthetic",
        "tier": "company",
        "row": {
            "primary_email": "contact@scottsdalemedspa.com",
            "company_name": "Scottsdale MedSpa & Laser",
            "first_name": "",
            "last_name": "",
            "outreach_tier": "company",
            "aevora_segment": "medical_aesthetic",
            "First_category": "Medical Spa",
            "City": "Scottsdale",
            "State": "AZ",
        },
        "research": {
            "evidence": "weak",
            "snippet": "Scottsdale medical spa treatments",
            "research_signal": "Scottsdale medical spa practice",
            "signal_strength": "weak",
        },
    },
]

samples = []
for tc in TEST_CASES:
    seq, variant = generate_sequence(tc["row"], tc["research"], pack)
    samples.append({
        "id": tc["id"],
        "segment": tc["segment"],
        "tier": tc["tier"],
        "evidence": tc["research"]["evidence"],
        "variant": variant,
        "email1": {"subject": seq[0][0], "body": seq[0][1]},
        "email2": {"subject": seq[1][0], "body": seq[1][1]},
        "email3": {"subject": seq[2][0], "body": seq[2][1]},
    })

print(json.dumps(samples, indent=2))

