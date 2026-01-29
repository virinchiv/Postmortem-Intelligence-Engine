from crewai import Crew
from agents.ingestion_agent import ingestion_agent
from agents.pattern_agent import pattern_agent
from agents.risk_agent import risk_agent
from agents.explanation_agent import explanation_agent
from crew.tasks import tasks

crew = Crew(
    agents=[
        ingestion_agent,
        pattern_agent,
        risk_agent,
        explanation_agent
    ],
    tasks=tasks,
    verbose=True
)