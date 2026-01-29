from crewai import Agent

pattern_agent = Agent (
    role="Failure Pattern Mining Agent",
    goal="Identify recurring failure patterns across historical incidents",
    backstory=(
        "You analyze historical incidents to uncover repeated failure motifs "
        "such as cascading retries, shared dependency failures, and unsafe rollouts."
    ),
    allow_delegation=False,
    verbose=True
)