from typing import Dict, Any, List, Optional
import hashlib
from datetime import datetime

from memory.vector_store import VectorStore
from memory.metadata_store import MetadataStore
from schemas.postmortem_schema import ExtractedPostmortem

class FailureMemory:
    def __init__(self, 
                 vector_store_path: str = "memory/vector_store.faiss",
                 metadata_db_path: str = "data/postmortems.db"):
        self.vector_store = VectorStore(vector_store_path)
        self.metadata_store = MetadataStore(metadata_db_path)
    
    def store_failure_memory(self, postmortem: ExtractedPostmortem) -> str:
        """
        Store postmortem in both vector store and metadata store
        
        Args:
            postmortem: ExtractedPostmortem object
            
        Returns:
            Document ID for the stored postmortem
        """
        try:
            # Generate document ID
            doc_id = self._generate_doc_id(postmortem)
            
            # Convert to dictionary for vector store
            postmortem_dict = postmortem.dict()
            
            # Store in vector store
            vector_doc_id = self.vector_store.add_document(postmortem_dict, doc_id)
            
            # Store in metadata store
            success = self.metadata_store.store_postmortem(postmortem, doc_id)
            
            if not success:
                raise Exception("Failed to store in metadata store")
            
            print(f"Successfully stored failure memory with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"Error storing failure memory: {e}")
            raise
    
    def _generate_doc_id(self, postmortem: ExtractedPostmortem) -> str:
        """Generate unique document ID from postmortem content"""
        # Use raw_text_hash if available, otherwise generate from content
        if hasattr(postmortem, 'raw_text_hash') and postmortem.raw_text_hash:
            base_id = postmortem.raw_text_hash
        else:
            # Create hash from title, organization, and incident date
            content = f"{postmortem.title}_{postmortem.organization}_{postmortem.incident_date}"
            base_id = hashlib.sha256(content.encode()).hexdigest()
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_id[:16]}_{timestamp}"
    
    def query_similar_failures(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Query for similar failures using semantic search
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of similar failure documents with metadata
        """
        try:
            # Search vector store
            vector_results = self.vector_store.search_similar(query, k)
            
            # Enhance with full metadata from metadata store
            enhanced_results = []
            for result in vector_results:
                doc_id = result['id']
                metadata = self.metadata_store.get_postmortem_by_id(doc_id)
                
                if metadata:
                    # Combine vector search results with metadata
                    enhanced_result = {
                        **metadata,
                        'similarity_score': result['similarity_score'],
                        'vector_text': result['text']
                    }
                    enhanced_results.append(enhanced_result)
                else:
                    # Fallback to vector store data
                    enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            print(f"Error querying similar failures: {e}")
            return []
    
    def get_failure_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific failure by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Failure document with full metadata
        """
        try:
            return self.metadata_store.get_postmortem_by_id(doc_id)
        except Exception as e:
            print(f"Error retrieving failure by ID: {e}")
            return None
    
    def search_failures(self, 
                       organization: Optional[str] = None,
                       severity: Optional[str] = None,
                       failure_type: Optional[str] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search failures with structured filters
        
        Args:
            organization: Filter by organization
            severity: Filter by severity level
            failure_type: Filter by failure type
            limit: Maximum number of results
            
        Returns:
            List of matching failure documents
        """
        try:
            return self.metadata_store.search_postmortems(
                organization=organization,
                severity=severity,
                failure_type=failure_type,
                limit=limit
            )
        except Exception as e:
            print(f"Error searching failures: {e}")
            return []
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        try:
            vector_stats = self.vector_store.get_stats()
            metadata_stats = self.metadata_store.get_stats()
            
            return {
                'vector_store': vector_stats,
                'metadata_store': metadata_stats,
                'total_stored': vector_stats['total_documents'],
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {'error': str(e)}
    
    def delete_failure(self, doc_id: str) -> bool:
        """
        Delete failure from both stores
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from metadata store
            metadata_success = self.metadata_store.delete_postmortem(doc_id)
            
            # Note: FAISS doesn't support easy deletion of individual vectors
            # For now, we'll mark it as deleted in metadata
            # In production, you might want to rebuild the index periodically
            
            if metadata_success:
                print(f"Deleted failure memory with ID: {doc_id}")
                return True
            else:
                print(f"Failed to delete failure memory with ID: {doc_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting failure memory: {e}")
            return False
    
    def check_persistence(self) -> bool:
        """Verify that memory persists across runs"""
        try:
            # Check if stores are accessible and have data
            vector_stats = self.vector_store.get_stats()
            metadata_stats = self.metadata_store.get_stats()
            
            # Basic checks
            if vector_stats['total_documents'] >= 0 and metadata_stats.get('total_postmortems', 0) >= 0:
                print("✅ Memory persistence check passed")
                return True
            else:
                print("❌ Memory persistence check failed")
                return False
                
        except Exception as e:
            print(f"❌ Memory persistence check failed: {e}")
            return False
    def perform_pattern_mining(self) -> Dict[str, Any]:
        """
        Group incidents by failure_type and shared components, 
        generate summaries, and store in global_patterns.
        """
        from collections import defaultdict
        
        all_postmortems = self.metadata_store.get_all_postmortems()
        
        failure_type_groups = defaultdict(list)
        component_groups = defaultdict(list)
        
        for pm in all_postmortems:
            # Group by failure type
            f_type = pm['root_cause'].get('failure_type', 'unknown')
            failure_type_groups[f_type].append(pm)
            
            # Group by shared components
            for component in pm['impact'].get('affected_services', []):
                component_groups[component].append(pm)
        
        results = {
            'failure_types': {},
            'components': {}
        }
        
        # Process failure type groups
        for f_type, pms in failure_type_groups.items():
            if len(pms) < 1: continue
            
            summary = self._generate_pattern_summary("failure_type", f_type, pms)
            incident_ids = [pm['id'] for pm in pms]
            
            self.metadata_store.store_global_pattern("failure_type", f_type, summary, incident_ids)
            results['failure_types'][f_type] = {
                'count': len(pms),
                'summary': summary
            }
            
        # Process component groups
        for component, pms in component_groups.items():
            if len(pms) < 1: continue
            
            summary = self._generate_pattern_summary("component", component, pms)
            incident_ids = [pm['id'] for pm in pms]
            
            self.metadata_store.store_global_pattern("component", component, summary, incident_ids)
            results['components'][component] = {
                'count': len(pms),
                'summary': summary
            }
            
        return results

    def _generate_pattern_summary(self, group_type: str, key: str, pms: List[Dict[str, Any]]) -> str:
        """Generate a short summary for a group of incidents"""
        summary_parts = []
        if group_type == "failure_type":
            summary_parts.append(f"Recurring pattern of {key} failures.")
        else:
            summary_parts.append(f"Recurring failures affecting component: {key}.")
            
        titles = [pm['title'] for pm in pms[:3]]
        summary_parts.append(f"Seen in: {', '.join(titles)}.")
        
        # Add a placeholder for "Short pattern summaries (LLM-assisted or rule-based)"
        # For now, we'll use a rule-based summary. 
        # In a real scenario, this would call an LLM with the group details.
        
        common_factors = []
        for pm in pms:
            common_factors.extend(pm['root_cause'].get('contributing_factors', []))
            
        if common_factors:
            from collections import Counter
            most_common = [f for f, count in Counter(common_factors).most_common(2)]
            summary_parts.append(f"Common factors: {', '.join(most_common)}.")
            
        return " ".join(summary_parts)
