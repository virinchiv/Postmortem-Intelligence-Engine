from memory.failure_memory import FailureMemory
from schemas.postmortem_schema import ExtractedPostmortem, RootCause, Impact, TimelineEvent, RemediationAction, SeverityLevel, ImpactScope, FailureType
from datetime import datetime
import json

def seed_data(memory):
    print("🌱 Seeding sample postmortem data...")
    
    samples = [
        {
            "title": "Cloudflare Flowspec Bug",
            "organization": "Cloudflare",
            "incident_date": datetime(2013, 3, 3),
            "severity": SeverityLevel.CRITICAL,
            "root_cause": {
                "primary_cause": "Invalid Flowspec rule for packet length",
                "technical_details": "Routers consumed RAM and crashed when encountering large packet length rules.",
                "failure_type": FailureType.CONFIGURATION_ERROR,
                "contributing_factors": ["DDoS attack", "Edge router bug"]
            },
            "impact": {
                "affected_services": ["Edge Network", "DNS"],
                "user_impact": "Global network outage",
                "duration_minutes": 30,
                "scope": ImpactScope.FULL_OUTAGE
            },
            "timeline": [],
            "remediation_actions": [],
            "detected_patterns": [],
            "summary": "Network-wide outage due to Flowspec rule.",
            "lessons_learned": [],
            "raw_text_hash": "hash1",
            "extraction_timestamp": datetime.now(),
            "confidence_score": 1.0
        },
        {
            "title": "Cloudflare BGP Route Leak",
            "organization": "Cloudflare",
            "incident_date": datetime(2020, 7, 17),
            "severity": SeverityLevel.HIGH,
            "root_cause": {
                "primary_cause": "Configuration error in backbone router",
                "technical_details": "Deactivating prefix-list instead of term leaked all BGP routes.",
                "failure_type": FailureType.CONFIGURATION_ERROR,
                "contributing_factors": ["Human error", "Backbone congestion"]
            },
            "impact": {
                "affected_services": ["Backbone Network", "CDN"],
                "user_impact": "50% traffic drop in certain geographies",
                "duration_minutes": 27,
                "scope": ImpactScope.PARTIAL_OUTAGE
            },
            "timeline": [],
            "remediation_actions": [],
            "detected_patterns": [],
            "summary": "Backbone outage due to BGP leak.",
            "lessons_learned": [],
            "raw_text_hash": "hash2",
            "extraction_timestamp": datetime.now(),
            "confidence_score": 1.0
        },
        {
            "title": "Cloudflare Service Token Corruption",
            "organization": "Cloudflare",
            "incident_date": datetime(2023, 1, 24),
            "severity": SeverityLevel.HIGH,
            "root_cause": {
                "primary_cause": "Metadata overwrite during release",
                "technical_details": "Read operation redacted secrets, which were then written back as empty strings.",
                "failure_type": FailureType.DEPLOYMENT_ERROR,
                "contributing_factors": ["Redaction logic bug", "Lack of empty string check"]
            },
            "impact": {
                "affected_services": ["Authentication", "WARP", "API", "R2"],
                "user_impact": "Service token authentication failures",
                "duration_minutes": 121,
                "scope": ImpactScope.CUSTOMER_FACING
            },
            "timeline": [],
            "remediation_actions": [],
            "detected_patterns": [],
            "summary": "Authentication failure due to metadata bug.",
            "lessons_learned": [],
            "raw_text_hash": "hash3",
            "extraction_timestamp": datetime.now(),
            "confidence_score": 1.0
        },
        {
            "title": "Allegro Flash Sale Crash",
            "organization": "Allegro",
            "incident_date": datetime(2018, 7, 18),
            "severity": SeverityLevel.HIGH,
            "root_cause": {
                "primary_cause": "Resource reservation gridlock",
                "technical_details": "Excessive resource reservations prevented scaling despite available capacity.",
                "failure_type": FailureType.CONFIGURATION_ERROR,
                "contributing_factors": ["High traffic", "Scaling misconfiguration"]
            },
            "impact": {
                "affected_services": ["Search", "Listing", "Opbox"],
                "user_impact": "Site unavailable for 20 minutes",
                "duration_minutes": 20,
                "scope": ImpactScope.FULL_OUTAGE
            },
            "timeline": [],
            "remediation_actions": [],
            "detected_patterns": [],
            "summary": "Site crash during flash sale.",
            "lessons_learned": [],
            "raw_text_hash": "hash4",
            "extraction_timestamp": datetime.now(),
            "confidence_score": 1.0
        }
    ]
    
    for sample in samples:
        pm = ExtractedPostmortem(**sample)
        memory.store_failure_memory(pm)
        
    print(f"✅ Seeded {len(samples)} postmortems.")

def run_pattern_mining():
    print("\n🔍 Running Pattern Mining Clustering...")
    memory = FailureMemory()
    
    # Ensure some data exists
    stats = memory.get_memory_stats()
    if stats['metadata_store']['total_postmortems'] == 0:
        seed_data(memory)
        
    # Perform pattern mining
    results = memory.perform_pattern_mining()
    
    print("\n📊 Pattern Mining Results:")
    print("-" * 30)
    
    print("\n[Grouped by Failure Type]")
    for f_type, data in results['failure_types'].items():
        print(f"🔹 {f_type} ({data['count']} incidents):")
        print(f"   Summary: {data['summary']}")
        
    print("\n[Grouped by Shared Component]")
    for component, data in results['components'].items():
        if data['count'] > 1: # Only show recurring components
            print(f"🔸 {component} ({data['count']} incidents):")
            print(f"   Summary: {data['summary']}")
            
    # Verify persistence in memory
    print("\n💾 Verifying persistence in global_patterns table...")
    global_patterns = memory.metadata_store.get_global_patterns()
    print(f"   Found {len(global_patterns)} global patterns stored in memory.")

if __name__ == "__main__":
    run_pattern_mining()
