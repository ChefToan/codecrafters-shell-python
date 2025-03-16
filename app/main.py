import sys
import os

def main():
    builtins = {"echo", "exit", "type"}

    while True:
        command = input("$ ")
        parts = command.strip().split()
        
        if parts and parts[0] == "exit":
            exit_code = 0
            if len(parts) > 1:
                try:
                    exit_code = int(parts[1])
                except ValueError:
                    exit_code = 1
            sys.exit(exit_code)

        if parts and parts[0] == "echo":
            print(" ".join(parts[1:]))
            continue

        if parts and parts[0] == "type":
            if len(parts) > 1:
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
            else:
                print("type: missing argument")
            continue

        print(f"{command}: command not found")

if __name__ == "__main__":
    main()
