import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MODULES = [
    "torch",
    "transformers",
    "peft",
    "bitsandbytes",
    "huggingface_hub",
    "student_local.common",
]


def main() -> int:
    for module_name in MODULES:
        start = time.perf_counter()
        print(f"import start: {module_name}", flush=True)
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            elapsed = time.perf_counter() - start
            print(f"import failed: {module_name} after {elapsed:.2f}s", flush=True)
            print(f"reason: {type(exc).__name__}: {exc}", flush=True)
            return 1
        elapsed = time.perf_counter() - start
        version = getattr(module, "__version__", "unknown")
        print(f"import ok: {module_name} version={version} elapsed={elapsed:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
