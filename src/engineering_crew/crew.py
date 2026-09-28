import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.sandbox_tools import sandbox_tools
from dotenv import load_dotenv

load_dotenv(override = True)

llm = LLM(
    model = os.getenv("MODEL"),
)

@CrewBase
class EngineeringCrew():
    """EngineeringCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config = self.agents_config['backend_engineer'], # type: ignore[index]
            verbose = True,
            tools = sandbox_tools,
            mcps = ["https://mcp.context7.com/mcp"]
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config = self.agents_config['frontend_engineer'], # type: ignore[index]
            verbose = True,
            tools = sandbox_tools,
            mcps = ["https://mcp.context7.com/mcp"]
        )

    @agent
    def testing_engineer(self) -> Agent:
        return Agent(
            config = self.agents_config['testing_engineer'], # type: ignore[index]
            verbose = True,
            tools = sandbox_tools,
            mcps = ["https://mcp.context7.com/mcp"]
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'], # type: ignore[index]
        )

    @task
    def ui_task(self) -> Task:
        return Task(
            config=self.tasks_config['ui_task'], # type: ignore[index]
        )

    @task
    def testing_task(self) -> Task:
        return Task(
            config=self.tasks_config['testing_task'], # type: ignore[index]
            output_file='mnt/testing_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringCrew crew"""
        
        manager_agent = Agent(
            config=self.agents_config["engineering_leader"],
            allow_delegation = True,
            llm = llm
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent = manager_agent,
            tracing = True,
            max_rpm = 15
        )
