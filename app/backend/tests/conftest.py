import os
import sys
import tempfile
from pathlib import Path

os.environ["HUNTBOARD_DATA_DIR"] = tempfile.mkdtemp(prefix="huntboard-test-")
os.environ["VEILLE_ENABLED"] = "false"
os.environ["APP_PASSWORD"] = ""
os.environ["LLM_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
