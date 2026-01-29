from crewai import Agent

ingestion_agent = Agent(
    role="Postmortem Ingestion Agent",
    goal="Extract structured failure data from incident postmortems",
    backstory=(
        "You are an SRE-focused AI agent specialized in reading postmortems "
        "and extracting root causes, contributing factors, and impacted systems."
    ),
    allow_delegation=False,
    verbose=True
)