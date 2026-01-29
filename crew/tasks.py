from crewai import Task

tasks = [
    Task(
        description="Parse postmortems and extract structured failure data",
        agent="Postmortem Ingestion Agent"
    ),
    Task(
        description="Analyze historical failures to identify recurring patterns",
        agent="Failure Pattern Mining Agent"
    ),
    Task(
        description="Evaluate new system design against known failures",
        agent="System Risk Analysis Agent"
    ),
    Task(
        description="Generate explainable risk reports with references to past incidents",
        agent="Explanation & Recommendation Agent"
    )
]