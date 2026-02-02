import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ingestion_agent import EnhancedIngestionAgent
import json
from datetime import datetime

def test_cloudflare_ingestion():
    # Initialize the ingestion agent
    agent = EnhancedIngestionAgent()
    
    # Test with Cloudflare postmortem
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Cloudfare #5.txt'), 'r') as f:
        cloudflare_text = f.read()
    
    print("Testing Cloudflare postmortem ingestion...")
    print("=" * 50)
    
    # Process the postmortem
    response = agent.process_postmortem(
        raw_text=cloudflare_text,
        organization="Cloudflare",
        source_url="https://blog.cloudflare.com/"
    )
    
    if response.success:
        print("✅ Ingestion successful!")
        print(f"Processing time: {response.processing_time_seconds:.2f} seconds")
        print(f"Confidence score: {response.extracted_data.confidence_score}")
        
        # Display extracted information
        data = response.extracted_data
        print(f"\n📋 Title: {data.title}")
        print(f"🏢 Organization: {data.organization}")
        print(f"📅 Incident Date: {data.incident_date}")
        print(f"🚨 Severity: {data.severity}")
        
        print(f"\n🔍 Root Cause:")
        print(f"  Primary: {data.root_cause.primary_cause}")
        print(f"  Type: {data.root_cause.failure_type}")
        print(f"  Contributing factors: {', '.join(data.root_cause.contributing_factors)}")
        
        print(f"\n💥 Impact:")
        print(f"  Services: {', '.join(data.impact.affected_services)}")
        print(f"  Duration: {data.impact.duration_minutes} minutes")
        print(f"  Scope: {data.impact.scope}")
        
        print(f"\n⏰ Timeline Events: {len(data.timeline)}")
        for event in data.timeline[:3]:  # Show first 3 events
            print(f"  {event.timestamp}: {event.description[:80]}...")
        
        print(f"\n🔧 Remediation Actions: {len(data.remediation_actions)}")
        for action in data.remediation_actions:
            print(f"  - {action.action} ({action.category})")
        
        print(f"\n🔮 Detected Patterns: {len(data.detected_patterns)}")
        for pattern in data.detected_patterns:
            print(f"  - {pattern.pattern_name}: {pattern.description[:60]}...")
        
        # Save to JSON for inspection
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_extraction_result.json'), 'w') as f:
            json.dump(data.dict(), f, indent=2, default=str)
        print(f"\n💾 Full result saved to test_extraction_result.json")
        
    else:
        print("❌ Ingestion failed!")
        print(f"Error: {response.error_message}")
        print(f"Processing time: {response.processing_time_seconds:.2f} seconds")

if __name__ == "__main__":
    test_cloudflare_ingestion()
