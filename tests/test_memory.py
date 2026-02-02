import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.failure_memory import FailureMemory
from agents.ingestion_agent import EnhancedIngestionAgent
import json

def test_memory_layer():
    print("🧠 Testing Memory Layer Implementation")
    print("=" * 50)
    
    # Initialize memory system
    memory = FailureMemory()
    
    # Check persistence
    print("1. Checking memory persistence...")
    persistence_ok = memory.check_persistence()
    print(f"   Persistence check: {'✅' if persistence_ok else '❌'}")
    
    # Get initial stats
    print("\n2. Initial memory stats:")
    stats = memory.get_memory_stats()
    print(f"   Vector store: {stats['vector_store']['total_documents']} documents")
    print(f"   Metadata store: {stats['metadata_store']['total_postmortems']} postmortems")
    
    # Test with existing extraction result
    print("\n3. Loading existing extraction result...")
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_extraction_result.json'), 'r') as f:
            extracted_data = json.load(f)
        
        print(f"   Loaded: {extracted_data['title']}")
        
        # Store in memory
        print("\n4. Storing in failure memory...")
        from schemas.postmortem_schema import ExtractedPostmortem
        
        # Convert dict to ExtractedPostmortem object
        postmortem = ExtractedPostmortem(**extracted_data)
        
        doc_id = memory.store_failure_memory(postmortem)
        print(f"   Stored with ID: {doc_id}")
        
        # Test retrieval
        print("\n5. Testing retrieval...")
        retrieved = memory.get_failure_by_id(doc_id)
        if retrieved:
            print(f"   ✅ Retrieved: {retrieved['title']}")
        else:
            print("   ❌ Failed to retrieve")
        
        # Test semantic search
        print("\n6. Testing semantic search...")
        similar = memory.query_similar_failures("service token authentication failure", k=3)
        print(f"   Found {len(similar)} similar failures")
        for i, result in enumerate(similar[:2]):
            print(f"   {i+1}. {result['title']} (similarity: {result.get('similarity_score', 0):.3f})")
        
        # Test structured search
        print("\n7. Testing structured search...")
        cloudflare_failures = memory.search_failures(organization="Cloudflare", limit=5)
        print(f"   Found {len(cloudflare_failures)} Cloudflare failures")
        
        # Final stats
        print("\n8. Final memory stats:")
        final_stats = memory.get_memory_stats()
        print(f"   Vector store: {final_stats['vector_store']['total_documents']} documents")
        print(f"   Metadata store: {final_stats['metadata_store']['total_postmortems']} postmortems")
        
        print(f"\n✅ Memory layer test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during memory test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_memory_layer()
