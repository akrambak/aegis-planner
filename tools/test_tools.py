import sys
from pathlib import Path

# Add project root to PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.shell.runner import run

print(run(["pwd"]))
print(run(["ls"]))
