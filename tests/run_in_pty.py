import pty
import sys

def main():
    # Command to run inside PTY
    cmd = ["python", "tests/run_tests.py"]

    # Spawn PTY
    status = pty.spawn(cmd)

    # Extract real exit code from wait status
    exit_code = status >> 8

    # Exit with correct code so GitHub Actions fails on test failures
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
