# Engineering Crew

A multi-agent software engineering workflow built with CrewAI.

The project uses one Engineering Lead and three specialized engineering agents to turn a natural-language requirement into a working Python application. The agents share a sandboxed development environment, inspect current documentation when needed, install required libraries, write code, and verify the result before completing the task.

## How It Works

The crew is organized around a simple engineering workflow:

```text
User Requirements
       |
Engineering Lead
       |
       |-------------------|
Backend Engineer     Frontend Engineer
       |-------------------|
                 |
          Testing Engineer
                 |
          Tested Application
```

The Engineering Lead is responsible for architecture and coordination. The other agents implement the design rather than independently deciding how the project should be structured.

### Engineering Lead

The lead acts as the technical owner of the generated project.

It defines:

* Project structure
* Modules and responsibilities
* Classes and functions
* Function signatures and interfaces
* Agent ownership
* Implementation order
* Dependencies for `pyproject.toml`
* UI direction
* Testing strategy
* Current third-party API guidance

The goal is to eliminate ambiguity before implementation starts.

### Backend Engineer

The backend engineer implements the backend according to the lead's design.

The backend is intentionally restricted to the Python standard library. It does not add third-party dependencies or UI code.

The agent also uses the sandbox to write and verify its implementation before handing the project to the next stage.

### Frontend Engineer

The frontend engineer builds the application UI using Gradio.

The UI is implemented as a single Python file alongside the backend and follows the architecture and visual direction defined by the Engineering Lead.

The agent also creates a separate validation script that imports and instantiates the Gradio `Blocks` application. The validation process does not call `.launch()`.

### Testing Engineer

The testing engineer writes and runs the backend test suite using the framework selected by the Engineering Lead.

Tests are executed inside the sandbox and are iterated until they pass.

When a backend issue is discovered, the testing agent can make a minimal fix after checking the interfaces used by the frontend.

## Execution Environment

Agents do not work only from their model knowledge.

Each engineering task is executed inside a sandbox with:

* A `uv` Python environment
* Internet access
* A Docker-based execution environment
* Access to the filesystem for creating and modifying project files
* The ability to inspect current library documentation
* The ability to install libraries required by the generated project

The execution environment is based on a Python image and is intentionally restricted to Python tooling.

This means an agent may investigate APIs or retrieve information from the internet during development, but the actual project execution environment remains Python-based.

## Current API Awareness

Library APIs change.

Instead of relying entirely on previously learned API patterns, the Engineering Lead is instructed to verify the current APIs of third-party libraries before giving implementation instructions to the other agents.

The resulting design contains the relevant API guidance so downstream agents can implement against the verified interface.

This is particularly important for frameworks such as Gradio where APIs and component patterns can change between releases.

## Generated Project

The agents write their work into the `mnt` workspace.

The current generated application is a small ERP example:

```text
mnt/
├── tiny_erp/
│   ├── database.py
│   ├── models.py
│   ├── services.py
│   ├── tax.py
│   └── ui.py
├── README.md
├── main.py
├── pyproject.toml
├── test_erp.py
├── test_ui.py
├── testing_report.md
└── uv.lock
```

The exact structure of this directory is not hard-coded into the crew. It is produced from the Engineering Lead's design for each request.
The model used for this run was `gemini-3.5-flash-lite`, so the resulting implementation should also be viewed in that context; a less capable model may produce a simpler result than a stronger model would.

## Repository Structure

```text
engineering-crew/
├── knowledge/
│   └── user_preference.txt
├── mnt/
│   └── generated projects and validation artifacts
├── src/
│   └── engineering_crew/
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       ├── tools/
│       │   ├── __init__.py
│       │   └── sandbox_tools.py
│       ├── __init__.py
│       ├── crew.py
│       └── main.py
├── tests/
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── pyproject.toml
└── uv.lock
```

### `src/engineering_crew`

This is the actual CrewAI application.

`crew.py` defines the crew and task orchestration.

`main.py` provides the application entry point.

`config/agents.yaml` contains the agent definitions and responsibilities.

`config/tasks.yaml` defines the workflow and task dependencies.

## Task Flow

A typical run follows this sequence:

```text
1. Receive requirements
        |
2. Engineering Lead designs the system
        |
3. Backend Engineer implements the backend
        |
4. Frontend Engineer builds and validates the UI
        |
5. Testing Engineer writes and runs tests
        |
6. Final generated project + testing report
```

The tasks intentionally pass context between agents.

The frontend receives the backend task as context so the UI can be built against the actual implementation.
The testing task receives both backend and frontend context so backend changes can be made without accidentally breaking the UI contract.

## Installation

This project uses `uv`.

Clone the repository and install the environment:

```bash
git clone https://github.com/Shaahmir/Engineering-Crew.git
cd Engineering-Crew
uv sync
```

## Running the Crew

Run the main application with:

```bash
uv run python -m engineering_crew.main
```

The generated project and task artifacts are written under `mnt/`.
Docker must be installed and running on the host machine because the agents use a Docker-based sandbox to execute commands and validate generated code.

## License

This project is licensed under the MIT License.

---
