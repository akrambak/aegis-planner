import subprocess

ALLOWED_COMMANDS = {
    "ls",
    "pwd",
    "git",
    "python",
    "pytest",
    "node",
    "npm",
    "cat",
    "echo"
}

def run(command: list):
    if command[0] not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command '{command[0]}' not allowed")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }
