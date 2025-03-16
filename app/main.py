import os
import sys
import subprocess

def main():
    builtins = {"echo", "exit", "type"}

    while True:
        command = input("$ ")
        parts = command.strip().split()

        if not parts:
            continue

        if parts[0] == "exit":
            exit_code = 0
            if len(parts) > 1:
                try:
                    exit_code = int(parts[1])
                except ValueError:
                    exit_code = 1
            sys.exit(exit_code)

        if parts[0] == "echo":
            print(" ".join(parts[1:]))
            continue

        if parts[0] == "type":
            if len(parts) < 2:
                print("type: missing argument")
                continue

            cmd = parts[1]
            if cmd in builtins:
                print(f"{cmd} is a shell builtin")
            else:
                path_env = os.environ.get("PATH", "")
                found = False
                for directory in path_env.split(":"):
                    file_path = os.path.join(directory, cmd)
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        print(f"{cmd} is {file_path}")
                        found = True
                        break
                if not found:
                    print(f"{cmd}: not found")
            continue

        path_env = os.environ.get("PATH", "")
        executed = False
        for directory in path_env.split(":"):
            file_path = os.path.join(directory, parts[0])
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                try:
                    new_args = [os.path.basename(file_path)] + parts[1:]
                    result = subprocess.run(new_args, executable=file_path, capture_output=True, text=True)
                    if result.stdout:
                        print(result.stdout.strip())
                    executed = True
                except Exception as e:
                    print(f"Error executing {parts[0]}: {e}")
                break
        if not executed:
            print(f"{' '.join(parts)}: command not found")

if __name__ == "__main__":
    main()