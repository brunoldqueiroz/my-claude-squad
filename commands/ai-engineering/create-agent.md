---
name: create-agent
description: Generate multi-agent system boilerplate
arguments:
  - name: name
    description: Name of the agent system
    required: true
  - name: framework
    description: "Framework to use (langgraph, crewai, autogen)"
    required: false
    default: langgraph
  - name: agents
    description: "Comma-separated list of agent roles (e.g., researcher,writer,reviewer)"
    required: false
---

# Create Multi-Agent System

Generate a multi-agent system structure with your choice of framework.

## Usage

```
/create-agent research-team
/create-agent content-crew --framework crewai --agents researcher,writer,editor
/create-agent workflow-system --framework langgraph
```

## What Gets Created

```
{name}/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py         # Base agent class
│   │   └── {role}.py       # Individual agents
│   ├── tools/
│   │   ├── __init__.py
│   │   └── common.py       # Shared tools
│   ├── state.py            # State management (LangGraph)
│   └── workflow.py         # Main workflow/crew
├── scripts/
│   └── run.py              # Entry point
├── tests/
│   └── test_agents.py      # Agent tests
├── requirements.txt
├── .env.example
└── README.md
```

## Framework Options

| Framework | Architecture | Best For |
|-----------|--------------|----------|
| `langgraph` | Graph-based | Complex workflows, cycles, state |
| `crewai` | Role-based | Team collaboration, delegation |
| `autogen` | Conversational | Research, debate, human-in-loop |

## Agent Assignment

This command uses the **agent-framework-specialist** agent.

## Example Generated Code

### LangGraph Workflow
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_agent: str
    iteration: int

def create_workflow():
    graph = StateGraph(AgentState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("reviewer", reviewer_node)

    graph.add_edge("researcher", "writer")
    graph.add_conditional_edges(
        "reviewer",
        should_revise,
        {"revise": "writer", "complete": END}
    )

    graph.set_entry_point("researcher")
    return graph.compile()
```

### CrewAI Team
```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Senior Researcher",
    goal="Find accurate information",
    backstory="Expert researcher with attention to detail",
    tools=[search_tool],
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Write clear, engaging content",
    backstory="Professional writer",
    llm=llm
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential
)
```
