# Postmortem Intelligence-Engine

Modern engineering organizations write detailed postmortems after system outages
and incidents, yet these documents are rarely reused to inform future decisions.
As teams evolve and systems grow more complex, institutional knowledge about past failures is often lost — leading to repeated incidents caused by the same patterns.

The Postmortem Intelligence Engine transforms historical incident reports into
structured organizational memory. Using a GenAI-powered, agent-based architecture
coordinated through an MCP server, the system extracts root causes and recurring
failure patterns from postmortems and proactively evaluates new system designs
against past incidents.

Rather than summarizing failures, the engine converts them into predictive,
explainable intelligence that helps engineers anticipate risks before incidents occur.

## Architecture Overview

The system is built around an MCP (Model Context Protocol) server that coordinates
multiple specialized AI agents and shared memory.

1. Postmortem documents are ingested by a dedicated ingestion agent that extracts structured failure data including root causes, contributing factors, and impacted components.

2. Extracted failures are stored in a long-term memory system combining vector
   embeddings and structured metadata.

3. A pattern mining agent analyzes historical incidents to identify recurring
   failure motifs such as cascading retries, shared dependencies, and unsafe deployments.

4. When a new system design or operational change is proposed, a risk analysis
   agent compares it against historical failure patterns.

5. An explanation agent produces human-readable risk reports that reference
   specific past incidents and explain why similar conditions led to outages.

This architecture enables proactive risk detection while preserving transparency
and human oversight.