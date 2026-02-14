#!/usr/bin/env python3
"""
End-to-end integration test for MCP server ingestion
"""

import asyncio
import json
import sys
import os
import glob
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ingestion_agent import EnhancedIngestionAgent
from memory.failure_memory import FailureMemory
from schemas.postmortem_schema import ExtractedPostmortem

class IntegrationTester:
    def __init__(self):
        self.ingestion_agent = EnhancedIngestionAgent()
        self.failure_memory = FailureMemory()
        self.results = []
    
    def load_postmortems(self):
        """Load all available postmortem files"""
        postmortems = []
        
        # Look for Cloudflare files
        cloudflare_files = glob.glob("Cloudfare*.txt")
        for file_path in cloudflare_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():  # Skip empty files
                        postmortems.append({
                            'filename': file_path,
                            'content': content,
                            'organization': 'Cloudflare'
                        })
            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")
        
        # Look for other files
        other_files = glob.glob("*.txt")
        for file_path in other_files:
            if file_path.startswith('Cloudfare'):
                continue  # Already processed
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        postmortems.append({
                            'filename': file_path,
                            'content': content,
                            'organization': 'Unknown'
                        })
            except Exception as e:
                print(f"❌ Error reading {file_path}: {e}")
        
        return postmortems
    
    async def test_ingestion(self, postmortem):
        """Test ingestion for a single postmortem"""
        print(f"\n🔍 Testing ingestion: {postmortem['filename']}")
        print("-" * 50)
        
        try:
            # Step 1: Ingest postmortem
            response = self.ingestion_agent.process_postmortem(
                raw_text=postmortem['content'],
                organization=postmortem['organization']
            )
            
            if response.success:
                print(f"✅ Ingestion successful!")
                print(f"   Title: {response.extracted_data.title}")
                print(f"   Severity: {response.extracted_data.severity}")
                print(f"   Failure Type: {response.extracted_data.root_cause.failure_type}")
                print(f"   Affected Services: {', '.join(response.extracted_data.impact.affected_services)}")
                print(f"   Processing Time: {response.processing_time_seconds:.2f}s")
                print(f"   Confidence: {response.extracted_data.confidence_score}")
                
                # Step 2: Store in memory
                try:
                    doc_id = self.failure_memory.store_failure_memory(response.extracted_data)
                    print(f"✅ Stored in memory with ID: {doc_id}")
                    
                    result = {
                        'filename': postmortem['filename'],
                        'success': True,
                        'title': response.extracted_data.title,
                        'doc_id': doc_id,
                        'processing_time': response.processing_time_seconds,
                        'confidence': response.extracted_data.confidence_score,
                        'severity': response.extracted_data.severity,
                        'failure_type': response.extracted_data.root_cause.failure_type
                    }
                    
                except Exception as e:
                    print(f"❌ Memory storage failed: {e}")
                    result = {
                        'filename': postmortem['filename'],
                        'success': False,
                        'error': f"Memory storage: {e}"
                    }
                
            else:
                print(f"❌ Ingestion failed: {response.error_message}")
                result = {
                    'filename': postmortem['filename'],
                    'success': False,
                    'error': response.error_message
                }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Test exception: {e}")
            result = {
                'filename': postmortem['filename'],
                'success': False,
                'error': f"Exception: {e}"
            }
            self.results.append(result)
            return result
    
    async def test_similarity_search(self):
        """Test similarity search with stored data"""
        print(f"\n🔍 Testing similarity search")
        print("-" * 30)
        
        test_queries = [
            "service token authentication",
            "database outage",
            "deployment failure",
            "configuration error"
        ]
        
        for query in test_queries:
            try:
                results = self.failure_memory.query_similar_failures(query, k=3)
                print(f"\nQuery: '{query}'")
                print(f"Found {len(results)} similar failures")
                
                for i, result in enumerate(results[:2]):  # Show top 2
                    print(f"  {i+1}. {result.get('title', 'Unknown')} (similarity: {result.get('similarity_score', 0):.3f})")
                
            except Exception as e:
                print(f"❌ Search failed for '{query}': {e}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Integration Test Summary")
        print("=" * 50)
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"Total tests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            print(f"\n✅ Successful ingestions:")
            for result in successful:
                print(f"   - {result['filename']}: {result['title']}")
                print(f"     Processing time: {result['processing_time']:.2f}s")
        
        if failed:
            print(f"\n❌ Failed ingestions:")
            for result in failed:
                print(f"   - {result['filename']}: {result['error']}")
        
        # Get memory stats
        try:
            stats = self.failure_memory.get_memory_stats()
            print(f"\n💾 Memory Statistics:")
            print(f"   Vector Store: {stats['vector_store']['total_documents']} documents")
            print(f"   Metadata Store: {stats['metadata_store']['total_postmortems']} postmortems")
        except Exception as e:
            print(f"\n❌ Could not get memory stats: {e}")

async def main():
    """Run integration tests"""
    print("🚀 Postmortem Intelligence Engine - Integration Test")
    print("=" * 60)
    
    tester = IntegrationTester()
    
    # Load postmortems
    postmortems = tester.load_postmortems()
    print(f"📁 Found {len(postmortems)} postmortem files")
    
    if not postmortems:
        print("❌ No postmortem files found. Make sure .txt files are in the project directory.")
        return
    
    # Test each postmortem
    for postmortem in postmortems:
        await tester.test_ingestion(postmortem)
    
    # Test similarity search
    await tester.test_similarity_search()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
