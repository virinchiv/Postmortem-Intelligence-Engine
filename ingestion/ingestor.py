import json
import hashlib
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import ValidationError

from schemas.postmortem_schema import (
    ExtractedPostmortem, 
    IngestionRequest, 
    IngestionResponse,
    RootCause,
    Impact,
    TimelineEvent,
    RemediationAction,
    FailurePattern,
    SeverityLevel,
    ImpactScope,
    FailureType
)


class PostmortemIngestor:
    def __init__(self, groq_api_key: str, model: str = "llama-3.1-8b-instant"):
        from groq import Groq
        self.client = Groq(api_key=groq_api_key)
        self.model = model
    
    def _create_extraction_prompt(self, raw_text: str) -> str:
        return f"""
        You are an expert SRE and incident analyst. Extract structured information from this postmortem report.
        
        Return ONLY a valid JSON object matching this exact schema. Do not include any explanations or text outside the JSON.
        
        {{
            "title": "Brief descriptive title",
            "organization": "Company name",
            "incident_date": "YYYY-MM-DDTHH:MM:SS",
            "severity": "low|medium|high|critical",
            "root_cause": {{
                "primary_cause": "Main technical reason for failure",
                "technical_details": "Specific technical explanation",
                "failure_type": "deployment_error|configuration_error|dependency_failure|infrastructure_failure|human_error|third_party_issue|security_issue|performance_issue|other",
                "contributing_factors": ["factor1", "factor2"]
            }},
            "impact": {{
                "affected_services": ["service1", "service2"],
                "user_impact": "Description of how users were affected",
                "duration_minutes": 123,
                "scope": "internal|customer_facing|partial_outage|full_outage",
                "metrics": {{"error_rate": "50%", "affected_users": "1000"}}
            }},
            "timeline": [
                {{
                    "timestamp": "YYYY-MM-DDTHH:MM:SS",
                    "description": "What happened",
                    "event_type": "detection|response|mitigation|resolution"
                }}
            ],
            "remediation_actions": [
                {{
                    "action": "Specific action taken",
                    "category": "technical|process|monitoring|training",
                    "owner": "Team or person responsible",
                    "status": "planned|in_progress|completed"
                }}
            ],
            "detected_patterns": [
                {{
                    "pattern_name": "Name of recurring pattern",
                    "description": "Description of the pattern",
                    "indicators": ["warning sign1", "warning sign2"],
                    "prevention_strategies": ["strategy1", "strategy2"]
                }}
            ],
            "summary": "Brief summary of the incident",
            "lessons_learned": ["lesson1", "lesson2"]
        }}
        
        POSTMORTEM TEXT:
        {raw_text}
        """
    
    def _extract_with_llm(self, raw_text: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise incident analyst. Return only valid JSON."},
                    {"role": "user", "content": self._create_extraction_prompt(raw_text)}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case there's extra text)
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return None
    
    def _validate_and_clean_data(self, data: Dict[str, Any], raw_text: str) -> Optional[ExtractedPostmortem]:
        try:
            # Add required metadata
            data['raw_text_hash'] = hashlib.sha256(raw_text.encode()).hexdigest()
            data['extraction_timestamp'] = datetime.now()
            data['confidence_score'] = 0.8  # Default confidence
            
            # Parse and validate with Pydantic
            extracted = ExtractedPostmortem(**data)
            return extracted
            
        except ValidationError as e:
            print(f"Validation failed: {e}")
            return None
        except Exception as e:
            print(f"Data cleaning failed: {e}")
            return None
    
    def ingest_postmortem(self, request: IngestionRequest) -> IngestionResponse:
        start_time = time.time()
        
        try:
            # Extract structured data using LLM
            raw_data = self._extract_with_llm(request.raw_text)
            if not raw_data:
                return IngestionResponse(
                    success=False,
                    error_message="Failed to extract data with LLM",
                    processing_time_seconds=time.time() - start_time
                )
            
            # Override with provided metadata if available
            if request.organization:
                raw_data['organization'] = request.organization
            if request.incident_date:
                raw_data['incident_date'] = request.incident_date.isoformat()
            
            # Validate and clean the extracted data
            extracted_data = self._validate_and_clean_data(raw_data, request.raw_text)
            if not extracted_data:
                return IngestionResponse(
                    success=False,
                    error_message="Failed to validate extracted data",
                    processing_time_seconds=time.time() - start_time
                )
            
            return IngestionResponse(
                success=True,
                extracted_data=extracted_data,
                processing_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return IngestionResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                processing_time_seconds=time.time() - start_time
            )
