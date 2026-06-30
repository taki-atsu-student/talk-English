from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "requirements.txt"
MODEL_NAME = "microsoft/DialoGPT-small"


def run_command(command: list[str]) -> None:
    print("\n$ " + " ".join(command))
    subprocess.check_call(command)


def install_requirements() -> None:
    print("Installing Python packages from backend/requirements.txt...")
    run_command([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def preload_model() -> None:
    print(f"Downloading model and tokenizer: {MODEL_NAME}")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    AutoTokenizer.from_pretrained(MODEL_NAME)
    AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    print("Model download complete.")


def init_language_tool() -> None:
    print("Initializing language_tool_python...")
    try:
        import language_tool_python
        language_tool_python.LanguageTool("en-US")
        print("language_tool_python is ready.")
    except Exception as exc:
        print("WARNING: language_tool_python initialization failed.")
        print("Grammar check may still work, but this step could not complete.")
        print(f"Error: {exc}")


def main() -> None:
    install_requirements()
    preload_model()
    init_language_tool()
    print("\nSetup finished.")
    print("Next, run `run_backend.bat` on Windows or `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`.")


if __name__ == "__main__":
    main()
