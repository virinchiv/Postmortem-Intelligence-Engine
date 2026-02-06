from memory.metadata_store import MetadataStore
import json

def report_patterns():
    store = MetadataStore()
    patterns = store.get_global_patterns()
    
    print("\n" + "="*80)
    print("      GLOBAL FAILURE PATTERN MINING REPORT")
    print("="*80)
    
    # Failure Types
    print("\n[ Recurring Failure Types ]")
    print("-" * 30)
    for p in patterns:
        if p['pattern_type'] == 'failure_type':
            print(f"🔹 Type: {p['group_key']}")
            print(f"   Summary: {p['summary']}")
            print(f"   Incidents: {len(p['incident_ids'])}")
            print()
            
    # Components
    print("\n[ Recurring Impacted Components ]")
    print("-" * 30)
    for p in patterns:
        if p['pattern_type'] == 'component':
            print(f"🔸 Component: {p['group_key']}")
            print(f"   Summary: {p['summary']}")
            print(f"   Incidents: {len(p['incident_ids'])}")
            print()

if __name__ == "__main__":
    report_patterns()
