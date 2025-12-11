import pty

def main():
    # Command to run inside PTY
    cmd = ["python", "tests/run_tests.py"]

    # Spawn PTY
    pty.spawn(cmd)

if __name__ == "__main__":
    main()
