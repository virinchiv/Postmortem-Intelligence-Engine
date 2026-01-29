from crewai import Agent

explanation_agent = Agent(
    role="Explanation & Recommendation Agent",
    goal="Generate clear, actionable explanations for detected risks",
    backstory=(
        "You translate technical risk signals into concise, human-readable insights "
        "that engineers can act on."
    ),
    allow_delegation=False,
    verbose=True
)