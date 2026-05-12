import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_FILE = BASE_DIR / "schema.sql"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
VENV_DIR = BASE_DIR / ".venv"


def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def run(command, check=True, shell=False):
    return subprocess.run(command, check=check, shell=shell, text=True)


def check_postgres():
    print(color("Checking PostgreSQL...", "94"))
    try:
        run(["pg_isready"])
        print(color("PostgreSQL is running.", "92"))
    except Exception:
        print(color("PostgreSQL is not responding. Please start PostgreSQL first.", "91"))
        sys.exit(1)


def create_database():
    print(color("Creating database if needed...", "94"))
    command = "psql -tc \"SELECT 1 FROM pg_database WHERE datname = 'poihs_db'\" | grep -q 1 || createdb poihs_db"
    run(command, shell=True)
    print(color("Database check complete.", "92"))


def run_schema():
    if SCHEMA_FILE.exists():
        print(color("Running schema.sql...", "94"))
        run(f"psql poihs_db < \"{SCHEMA_FILE}\"", shell=True)
        print(color("Schema loaded.", "92"))


def run_seed_files():
    for seed_file in sorted(BASE_DIR.glob("seed_*.sql")):
        print(color(f"Running {seed_file.name}...", "94"))
        run(f"psql poihs_db < \"{seed_file}\"", shell=True)
    print(color("Seed file step complete.", "92"))


def create_venv_and_install():
    print(color("Creating Python virtual environment...", "94"))
    run([sys.executable, "-m", "venv", str(VENV_DIR)])
    pip_path = VENV_DIR / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")
    print(color("Installing backend requirements...", "94"))
    run([str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)])
    print(color("Python packages installed.", "92"))


def print_next_steps():
    print()
    print(color("Setup complete!", "92"))
    print(color("Next steps:", "96"))
    print("1. Start backend:")
    print("   cd backend")
    print("   source .venv/bin/activate   (Mac/Linux)")
    print("   .venv\\Scripts\\activate      (Windows)")
    print("   uvicorn app.main:app --reload")
    print("2. Start frontend:")
    print("   cd frontend")
    print("   npm install")
    print("   npm run dev")


if __name__ == "__main__":
    check_postgres()
    create_database()
    run_schema()
    run_seed_files()
    create_venv_and_install()
    print_next_steps()
