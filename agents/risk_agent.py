from crewai import Agent

risk_agent = Agent(
    role="System Risk Analysis Agent",
    goal="Evaluate proposed system designs against known failure patterns",
    backstory=(
        "You are an experienced reliability engineer who predicts risks by "
        "comparing new architectures against historical failures."
    ),
    allow_delegation=False,
    verbose=True
)