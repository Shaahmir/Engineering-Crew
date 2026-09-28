import atexit
import subprocess
from crewai.tools import tool
from pathlib import Path

SANDBOX_DIR = Path(__file__).parents[3] / "mnt"
SANDBOX_DIR.mkdir(parents = True, exist_ok = True)
CONTAINER_NAME = "sandbox"
IGNORE = [".venv", ".git", "__pyacache__", "node_modules"]

def start_sandbox():

    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output = True,
    )

    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
             "-v", f"{str(SANDBOX_DIR)}:/mnt",
            "-w", "/mnt",
            "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
            "tail", "-f", "/dev/null"
        ],
        check = True,
        capture_output = True,
        text = True
    )

    if not (SANDBOX_DIR / "pyproject.toml").exists():

        init_result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "uv", "init"],
            capture_output = True,
            timeout = 120
        )

        if init_result.returncode != 0:
            stop_sandbox()
            raise RuntimeError(f"uv init failed (exit {init_result.returncode}:\n{init_result.stderr})")

def stop_sandbox():

    subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output = True)
    subprocess.run(["docker", "rm", CONTAINER_NAME], capture_output = True)

atexit.register(stop_sandbox)

@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """
    List the filenames currently in the sandbox directory.

    Args:
        No args!.
    Returns:
        A newline-separated list of filenames, or a message if the
        sandbox is empty.
    """
    if not SANDBOX_DIR.exists():
        return "The Sandbox is currently empty!"

    files = []

    for file in SANDBOX_DIR.rglob("*"):
        if any(part in IGNORE for part in file.parts):
            continue
            
        try:
            if file.is_file():
                files.append(str(file.relative_to(SANDBOX_DIR)))
        except OSError:
            continue

    files.sort()
    return "\n".join(files) if files else "The Sandbox is currently empty!"

@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """
    Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "src/main.py").
    Returns:
        The file's contents, or a message if the file does not exist.
    """
    requested = (SANDBOX_DIR / filename).resolve()
    sandbox_root = SANDBOX_DIR.resolve()

    try:
        requested.relative_to(sandbox_root)
    except ValueError:
        return "ACCESS DENIED: Path is outside of the sandbox!"

    if not requested.exists() or not requested.is_file():
        return f"No file found! (INFO: Verify that you have entered correct directory)"

    return requested.read_text()

@tool("Write File to Sandbox")
def write_sandbox_file(filename: str, content: str) -> str:
    """
    Write text to a file in the sandbox directory, replacing any existing
    file with the same name.

    Args:
        filename: The name of the file to write (e.g. "src/main.py").
        content: The text content to write.
    Returns:
        A confirmation message.
    """
    requested = (SANDBOX_DIR / filename).resolve()
    sandbox_root = SANDBOX_DIR.resolve()

    try:
        requested.relative_to(sandbox_root)
    except ValueError:
        return "ACCESS DENIED: Path is outside of the sandbox!"

    requested.parent.mkdir(parents = True, exist_ok = True)
    requested.write_text(content)

    return f"Successfully wrote to {requested}"

@tool("Execute the Python File in Sandbox")
def run_sandbox_file(filename: str) -> str:
    """
    Execute a Python file from the sandbox directory inside an ephemeral
    Docker container, with the sandbox mounted as the working directory,
    and return whatever the script printed to stdout.

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").
    Returns:
        The text printed to stdout by the executed script.
    """
    requested = (SANDBOX_DIR / filename).resolve()
    sandbox_root = SANDBOX_DIR.resolve()

    try:
        requested.relative_to(sandbox_root)
    except ValueError:
        return "ACCESS DENIED: Path is outside of the sandbox!"

    try:
        result = subprocess.run(
            [
                "docker", "exec",
                CONTAINER_NAME, "uv", "run",
                "python", filename
            ],
            capture_output = True,
            text = True,
            timeout = 240
        )
    except subprocess.TimeoutExpired:
        return "Execution timed out after 240s."

    if result.returncode != 0:
        return f"Execution failed (exit {result.returncode}:\n{result.stderr})"

    return result.stdout

sandbox_tools = [
    list_sandbox_files,
    read_sandbox_file,
    write_sandbox_file,
    run_sandbox_file
]

def _never_cache(*args, **kwargs) -> bool:
    return False

for sandbox_tool in sandbox_tools:
    sandbox_tool.cache_function = _never_cache
