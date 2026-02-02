from crewai import Agent, LLM
from ingestion.ingestor import PostmortemIngestor
from schemas.postmortem_schema import IngestionRequest, IngestionResponse
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Groq LLM for CrewAI
groq_llm = LLM(
    model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com"
)

ingestion_agent = Agent(
    role="Postmortem Ingestion Agent",
    goal="Extract structured failure data from incident postmortems",
    backstory=(
        "You are an SRE-focused AI agent specialized in reading postmortems "
        "and extracting root causes, contributing factors, and impacted systems."
    ),
    allow_delegation=False,
    verbose=True,
    llm=groq_llm
)

class EnhancedIngestionAgent:
    def __init__(self):
        self.ingestor = PostmortemIngestor(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
        )
    
    def process_postmortem(self, raw_text: str, organization: str = None, source_url: str = None) -> IngestionResponse:
        request = IngestionRequest(
            raw_text=raw_text,
            organization=organization,
            source_url=source_url
        )
        return self.ingestor.ingest_postmortem(request)