import os
import sys
import subprocess
import shlex

def main():
    builtins = {"echo", "exit", "type", "pwd", "cd"}

    while True:
        command = input("$ ")
        # Create a shlex lexer in posix mode for proper quoting handling
        lexer = shlex.shlex(command, posix=True)
        lexer.whitespace_split = True
        try:
            parts = list(lexer)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue

        if not parts:
            continue

        # Check for output redirection operators: > or 1>
        redir_file = None
        for idx, token in enumerate(parts):
            if token in (">", "1>"):
                if idx + 1 < len(parts):
                    redir_file = parts[idx + 1]
                    parts = parts[:idx]
                else:
                    print("Error: No file specified for redirection")
                break

        if not parts:
            continue

        # Process builtins and external commands
        if parts[0] == "exit":
            exit_code = 0
            if len(parts) > 1:
                try:
                    exit_code = int(parts[1])
                except ValueError:
                    exit_code = 1
            sys.exit(exit_code)

        if parts[0] == "echo":
            output = " ".join(parts[1:])
            if redir_file:
                with open(redir_file, "w") as f:
                    f.write(output + "\n")
            else:
                print(output)
            continue

        if parts[0] == "pwd":
            output = os.getcwd()
            if redir_file:
                with open(redir_file, "w") as f:
                    f.write(output + "\n")
            else:
                print(output)
            continue

        if parts[0] == "cd":
            if len(parts) < 2:
                print("cd: missing argument")
            else:
                path = parts[1]
                if path == "~":
                    home = os.environ.get("HOME")
                    if home:
                        path = home
                    else:
                        print("cd: HOME environment variable not set")
                        continue
                if os.path.isdir(path):
                    os.chdir(path)
                else:
                    print(f"cd: {path}: No such file or directory")
            continue

        if parts[0] == "type":
            if len(parts) < 2:
                print("type: missing argument")
                continue

            cmd = parts[1]
            if cmd in builtins:
                output = f"{cmd} is a shell builtin"
            else:
                path_env = os.environ.get("PATH", "")
                found = False
                for directory in path_env.split(":"):
                    file_path = os.path.join(directory, cmd)
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        output = f"{cmd} is {file_path}"
                        found = True
                        break
                if not found:
                    output = f"{cmd}: not found"
            if redir_file:
                with open(redir_file, "w") as f:
                    f.write(output + "\n")
            else:
                print(output)
            continue

        # External commands execution
        path_env = os.environ.get("PATH", "")
        executed = False
        for directory in path_env.split(":"):
            file_path = os.path.join(directory, parts[0])
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                try:
                    new_args = [os.path.basename(file_path)] + parts[1:]
                    result = subprocess.run(new_args, executable=file_path, capture_output=True, text=True)
                    if redir_file:
                        with open(redir_file, "w") as f:
                            f.write(result.stdout)
                    else:
                        if result.stdout:
                            print(result.stdout.strip())
                    if result.stderr:
                        sys.stderr.write(result.stderr)
                    executed = True
                except Exception as e:
                    print(f"Error executing {parts[0]}: {e}")
                break
        if not executed:
            print(f"{' '.join(parts)}: command not found")

if __name__ == "__main__":
    main()