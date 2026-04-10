import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")


def get_db_path() -> str:
    """Resolve the SQLite database path from any working directory."""
    return "clinic.db" if os.path.basename(os.getcwd()) == "Test" else "Test/clinic.db"
