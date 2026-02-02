import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from schemas.postmortem_schema import ExtractedPostmortem

class MetadataStore:
    def __init__(self, db_path: str = "data/postmortems.db"):
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create postmortems table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS postmortems (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    organization TEXT,
                    incident_date TEXT,
                    severity TEXT,
                    raw_text_hash TEXT UNIQUE,
                    extraction_timestamp TEXT,
                    confidence_score REAL,
                    summary TEXT,
                    root_cause TEXT,  -- JSON
                    impact TEXT,      -- JSON
                    timeline TEXT,    -- JSON
                    remediation_actions TEXT,  -- JSON
                    detected_patterns TEXT,    -- JSON
                    lessons_learned TEXT,       -- JSON array
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for common queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_organization ON postmortems(organization)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON postmortems(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_incident_date ON postmortems(incident_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_text_hash ON postmortems(raw_text_hash)')
            
            conn.commit()
            conn.close()
            print(f"Initialized metadata store at {self.db_path}")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def store_postmortem(self, postmortem: ExtractedPostmortem, doc_id: str) -> bool:
        """Store postmortem metadata in SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert complex objects to JSON
            root_cause_json = json.dumps(postmortem.root_cause.dict(), default=str)
            impact_json = json.dumps(postmortem.impact.dict(), default=str)
            timeline_json = json.dumps([event.dict() for event in postmortem.timeline], default=str)
            remediation_json = json.dumps([action.dict() for action in postmortem.remediation_actions], default=str)
            patterns_json = json.dumps([pattern.dict() for pattern in postmortem.detected_patterns], default=str)
            lessons_json = json.dumps(postmortem.lessons_learned, default=str)
            
            cursor.execute('''
                INSERT OR REPLACE INTO postmortems 
                (id, title, organization, incident_date, severity, raw_text_hash, 
                 extraction_timestamp, confidence_score, summary, root_cause, impact,
                 timeline, remediation_actions, detected_patterns, lessons_learned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                doc_id,
                postmortem.title,
                postmortem.organization,
                postmortem.incident_date.isoformat() if hasattr(postmortem.incident_date, 'isoformat') else str(postmortem.incident_date),
                postmortem.severity,
                postmortem.raw_text_hash,
                postmortem.extraction_timestamp.isoformat() if hasattr(postmortem.extraction_timestamp, 'isoformat') else str(postmortem.extraction_timestamp),
                postmortem.confidence_score,
                postmortem.summary,
                root_cause_json,
                impact_json,
                timeline_json,
                remediation_json,
                patterns_json,
                lessons_json
            ))
            
            conn.commit()
            conn.close()
            print(f"Stored postmortem metadata with ID: {doc_id}")
            return True
            
        except Exception as e:
            print(f"Error storing postmortem metadata: {e}")
            return False
    
    def get_postmortem_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve postmortem by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM postmortems WHERE id = ?', (doc_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                columns = [
                    'id', 'title', 'organization', 'incident_date', 'severity',
                    'raw_text_hash', 'extraction_timestamp', 'confidence_score',
                    'summary', 'root_cause', 'impact', 'timeline',
                    'remediation_actions', 'detected_patterns', 'lessons_learned',
                    'created_at', 'updated_at'
                ]
                
                result = dict(zip(columns, row))
                
                # Parse JSON fields
                result['root_cause'] = json.loads(result['root_cause'])
                result['impact'] = json.loads(result['impact'])
                result['timeline'] = json.loads(result['timeline'])
                result['remediation_actions'] = json.loads(result['remediation_actions'])
                result['detected_patterns'] = json.loads(result['detected_patterns'])
                result['lessons_learned'] = json.loads(result['lessons_learned'])
                
                return result
            
            return None
            
        except Exception as e:
            print(f"Error retrieving postmortem: {e}")
            return None
    
    def search_postmortems(self, 
                          organization: Optional[str] = None,
                          severity: Optional[str] = None,
                          failure_type: Optional[str] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Search postmortems with filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM postmortems WHERE 1=1"
            params = []
            
            if organization:
                query += " AND organization = ?"
                params.append(organization)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if failure_type:
                query += " AND JSON_EXTRACT(root_cause, '$.failure_type') = ?"
                params.append(failure_type)
            
            query += " ORDER BY incident_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            columns = [
                'id', 'title', 'organization', 'incident_date', 'severity',
                'raw_text_hash', 'extraction_timestamp', 'confidence_score',
                'summary', 'root_cause', 'impact', 'timeline',
                'remediation_actions', 'detected_patterns', 'lessons_learned',
                'created_at', 'updated_at'
            ]
            
            results = []
            for row in rows:
                result = dict(zip(columns, row))
                
                # Parse JSON fields
                result['root_cause'] = json.loads(result['root_cause'])
                result['impact'] = json.loads(result['impact'])
                result['timeline'] = json.loads(result['timeline'])
                result['remediation_actions'] = json.loads(result['remediation_actions'])
                result['detected_patterns'] = json.loads(result['detected_patterns'])
                result['lessons_learned'] = json.loads(result['lessons_learned'])
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching postmortems: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metadata store statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total count
            cursor.execute('SELECT COUNT(*) FROM postmortems')
            total_count = cursor.fetchone()[0]
            
            # Organizations
            cursor.execute('SELECT DISTINCT organization, COUNT(*) FROM postmortems GROUP BY organization')
            org_counts = dict(cursor.fetchall())
            
            # Severity distribution
            cursor.execute('SELECT severity, COUNT(*) FROM postmortems GROUP BY severity')
            severity_counts = dict(cursor.fetchall())
            
            # Failure types
            cursor.execute('SELECT JSON_EXTRACT(root_cause, "$.failure_type"), COUNT(*) FROM postmortems GROUP BY JSON_EXTRACT(root_cause, "$.failure_type")')
            failure_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_postmortems': total_count,
                'organizations': org_counts,
                'severity_distribution': severity_counts,
                'failure_type_distribution': failure_counts,
                'database_path': self.db_path
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'error': str(e)}
    
    def delete_postmortem(self, doc_id: str) -> bool:
        """Delete postmortem by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM postmortems WHERE id = ?', (doc_id,))
            affected_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                print(f"Deleted postmortem with ID: {doc_id}")
                return True
            else:
                print(f"No postmortem found with ID: {doc_id}")
                return False
                
        except Exception as e:
            print(f"Error deleting postmortem: {e}")
            return False
