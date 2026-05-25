import platform
import subprocess
import sys


def safe_run(command: list[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"unavailable ({exc})"


def main() -> None:
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"git commit: {safe_run(['git', 'rev-parse', '--short', 'HEAD'])}")
    try:
        import torch

        print(f"torch: {torch.__version__}")
        print(f"cuda available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"gpu: {torch.cuda.get_device_name(0)}")
            print(f"bf16 supported: {torch.cuda.is_bf16_supported()}")
            print(
                f"total memory (GiB): "
                f"{torch.cuda.get_device_properties(0).total_memory / (1024 ** 3):.2f}"
            )
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"torch import failed: {exc}")


if __name__ == "__main__":
    main()
