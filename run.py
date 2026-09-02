import os
import sys
import uvicorn
from pathlib import Path

# Configure utf-8 stdout for Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

if __name__ == "__main__":
    print("\n" + "="*75)
    print("  [JALDOOT] Machhuaare Ka Saathi , Samundar Ka Saarthi")
    print("="*75)
    print("  Bootstrapping database and running seed verification...")

    # Run DB seed
    try:
        from seed_data import seed
        seed()
        print("  Database initialized and seeded with demo vessels & hazards.")
    except Exception as e:
        print(f"  Seed warning: {e}")

    print("\n  Starting JalDoot Unified Server on: http://127.0.0.1:8000")
    print("  -------------------------------------------------------------------------")
    print("  ADMIN LOGIN       : admin@gmail.com / admin1234  -> Admin Dashboard")
    print("  FISHERMAN LOGIN   : ramesh_kumar / password123   -> Fisherman Mode")
    print("  API DOCUMENTATION : http://127.0.0.1:8000/docs")
    print("="*75 + "\n")

    # Start server with reload targeting only app folder
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False, app_dir=str(BACKEND_DIR))
