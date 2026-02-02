import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
import hashlib

# Simple embedding using TF-IDF as fallback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class VectorStore:
    def __init__(self, store_path: str = "memory/vector_store.faiss"):
        self.store_path = store_path
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.index = None
        self.documents = []  # Store document metadata
        self.dimension = 1000  # TF-IDF feature dimension
        self.is_fitted = False
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(store_path), exist_ok=True)
        
        # Load existing store if available
        self._load_store()
    
    def _load_store(self):
        """Load existing FAISS index and documents"""
        try:
            if os.path.exists(self.store_path):
                self.index = faiss.read_index(self.store_path)
                print(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
                
                # Load documents metadata
                docs_path = self.store_path.replace('.faiss', '_documents.pkl')
                if os.path.exists(docs_path):
                    with open(docs_path, 'rb') as f:
                        loaded_data = pickle.load(f)
                        self.documents = loaded_data['documents']
                        self.vectorizer = loaded_data['vectorizer']
                        self.is_fitted = loaded_data['is_fitted']
                    print(f"Loaded {len(self.documents)} document metadata entries")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.dimension)
                print("Created new FAISS index")
        except Exception as e:
            print(f"Error loading store: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.documents = []
            self.is_fitted = False
    
    def _save_store(self):
        """Save FAISS index and documents to disk"""
        try:
            faiss.write_index(self.index, self.store_path)
            
            # Save documents metadata and vectorizer
            docs_path = self.store_path.replace('.faiss', '_documents.pkl')
            save_data = {
                'documents': self.documents,
                'vectorizer': self.vectorizer,
                'is_fitted': self.is_fitted
            }
            with open(docs_path, 'wb') as f:
                pickle.dump(save_data, f)
                
            print(f"Saved FAISS index with {self.index.ntotal} vectors and {len(self.documents)} documents")
        except Exception as e:
            print(f"Error saving store: {e}")
    
    def _create_document_text(self, postmortem_data: Dict[str, Any]) -> str:
        """Create searchable text from postmortem data"""
        text_parts = []
        
        # Add title and summary
        if 'title' in postmortem_data:
            text_parts.append(f"Title: {postmortem_data['title']}")
        if 'summary' in postmortem_data:
            text_parts.append(f"Summary: {postmortem_data['summary']}")
        
        # Add root cause information
        if 'root_cause' in postmortem_data:
            rc = postmortem_data['root_cause']
            text_parts.append(f"Root Cause: {rc.get('primary_cause', '')}")
            text_parts.append(f"Technical Details: {rc.get('technical_details', '')}")
            text_parts.append(f"Failure Type: {rc.get('failure_type', '')}")
            if 'contributing_factors' in rc:
                text_parts.append(f"Contributing Factors: {' | '.join(rc['contributing_factors'])}")
        
        # Add impact information
        if 'impact' in postmortem_data:
            impact = postmortem_data['impact']
            text_parts.append(f"Affected Services: {' | '.join(impact.get('affected_services', []))}")
            text_parts.append(f"User Impact: {impact.get('user_impact', '')}")
            text_parts.append(f"Scope: {impact.get('scope', '')}")
        
        # Add remediation actions
        if 'remediation_actions' in postmortem_data:
            actions = postmortem_data['remediation_actions']
            action_texts = [f"{action.get('action', '')} ({action.get('category', '')})" for action in actions]
            text_parts.append(f"Remediation Actions: {' | '.join(action_texts)}")
        
        # Add detected patterns
        if 'detected_patterns' in postmortem_data:
            patterns = postmortem_data['detected_patterns']
            pattern_texts = [f"{pattern.get('pattern_name', '')}: {pattern.get('description', '')}" for pattern in patterns]
            text_parts.append(f"Patterns: {' | '.join(pattern_texts)}")
        
        # Add lessons learned
        if 'lessons_learned' in postmortem_data:
            lessons = postmortem_data['lessons_learned']
            text_parts.append(f"Lessons Learned: {' | '.join(lessons)}")
        
        return ' '.join(text_parts)
    
    def add_document(self, postmortem_data: Dict[str, Any], doc_id: str = None) -> str:
        """Add a document to the vector store"""
        if doc_id is None:
            # Create ID from content hash
            content_str = str(postmortem_data)
            doc_id = hashlib.md5(content_str.encode()).hexdigest()
        
        # Create searchable text
        document_text = self._create_document_text(postmortem_data)
        
        # Fit vectorizer if not already fitted
        if not self.is_fitted:
            all_texts = [doc['text'] for doc in self.documents] + [document_text]
            self.vectorizer.fit(all_texts)
            self.is_fitted = True
            
            # Re-index all existing documents
            if self.documents:
                self._rebuild_index()
        
        # Generate TF-IDF embedding
        embedding = self.vectorizer.transform([document_text]).toarray()
        embedding = embedding.astype('float32')
        
        # Resize if needed to match dimension
        if embedding.shape[1] < self.dimension:
            padding = np.zeros((1, self.dimension - embedding.shape[1]))
            embedding = np.hstack([embedding, padding])
        elif embedding.shape[1] > self.dimension:
            embedding = embedding[:, :self.dimension]
        
        # Add to FAISS index
        self.index.add(embedding)
        
        # Store document metadata
        doc_metadata = {
            'id': doc_id,
            'text': document_text,
            'postmortem_data': postmortem_data,
            'title': postmortem_data.get('title', ''),
            'organization': postmortem_data.get('organization', ''),
            'incident_date': postmortem_data.get('incident_date', ''),
            'severity': postmortem_data.get('severity', ''),
            'failure_type': postmortem_data.get('root_cause', {}).get('failure_type', ''),
            'affected_services': postmortem_data.get('impact', {}).get('affected_services', [])
        }
        
        self.documents.append(doc_metadata)
        
        # Save to disk
        self._save_store()
        
        print(f"Added document {doc_id} to vector store")
        return doc_id
    
    def _rebuild_index(self):
        """Rebuild the entire index with current documents"""
        if not self.documents:
            return
            
        # Get all document texts
        texts = [doc['text'] for doc in self.documents]
        
        # Generate embeddings for all documents
        embeddings = self.vectorizer.transform(texts).toarray()
        embeddings = embeddings.astype('float32')
        
        # Resize embeddings to match dimension
        if embeddings.shape[1] < self.dimension:
            padding = np.zeros((embeddings.shape[0], self.dimension - embeddings.shape[1]))
            embeddings = np.hstack([embeddings, padding])
        elif embeddings.shape[1] > self.dimension:
            embeddings = embeddings[:, :self.dimension]
        
        # Create new index and add all embeddings
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.index.ntotal == 0 or not self.is_fitted:
            return []
        
        # Generate query embedding
        query_embedding = self.vectorizer.transform([query]).toarray()
        query_embedding = query_embedding.astype('float32')
        
        # Resize if needed to match dimension
        if query_embedding.shape[1] < self.dimension:
            padding = np.zeros((1, self.dimension - query_embedding.shape[1]))
            query_embedding = np.hstack([query_embedding, padding])
        elif query_embedding.shape[1] > self.dimension:
            query_embedding = query_embedding[:, :self.dimension]
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(1 / (1 + dist))  # Convert distance to similarity
                results.append(doc)
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID"""
        for doc in self.documents:
            if doc['id'] == doc_id:
                return doc
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal,
            'dimension': self.dimension,
            'store_path': self.store_path
        }
