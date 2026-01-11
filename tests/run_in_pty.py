import pty
import sys


def main() -> None:
    # Command to run inside PTY
    cmd: list[str] = ['python', 'tests/run_tests.py']

    # Spawn PTY
    status: int = pty.spawn(cmd)

    # Extract real exit code from wait status
    exit_code: int = status >> 8

    # Exit with correct code so GitHub Actions fails on test failures
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
