import os
import sys
import subprocess
import shlex


def main():
    builtins = {"echo", "exit", "type", "pwd", "cd"}

    while True:
        command = input("$ ")
        lexer = shlex.shlex(command, posix=True)
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue

        if not tokens:
            continue

        # Parse redirection operators for stdout and stderr
        redir_stdout = None
        redir_stderr = None
        new_parts = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token in (">", "1>"):
                if i + 1 < len(tokens):
                    redir_stdout = tokens[i + 1]
                    i += 2
                    continue
                else:
                    print("Error: No file specified for redirection")
                    break
            elif token == "2>":
                if i + 1 < len(tokens):
                    redir_stderr = tokens[i + 1]
                    i += 2
                    continue
                else:
                    print("Error: No file specified for redirection")
                    break
            else:
                new_parts.append(token)
                i += 1

        if not new_parts:
            continue

        parts = new_parts

        # Ensure directories exist for redirected files
        def ensure_dir_exists(file_path):
            dir_path = os.path.dirname(file_path)
            if dir_path:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    return True
                except Exception as e:
                    print(f"Error creating directory {dir_path}: {e}")
                    return False
            return True

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

            # Create stderr redirection file even if it will be empty
            if redir_stderr is not None:
                ensure_dir_exists(redir_stderr)
                with open(redir_stderr, "w") as f:
                    pass  # Create empty file

            # Handle stdout as before
            if redir_stdout is not None:
                if ensure_dir_exists(redir_stdout):
                    with open(redir_stdout, "w") as f:
                        f.write(output + "\n")
                else:
                    print(output)
            else:
                print(output)
            continue

        if parts[0] == "pwd":
            output = os.getcwd()
            if redir_stdout is not None:
                if ensure_dir_exists(redir_stdout):
                    with open(redir_stdout, "w") as f:
                        f.write(output + "\n")
                else:
                    print(output)
            else:
                print(output)
            continue

        if parts[0] == "cd":
            if len(parts) < 2:
                error_msg = "cd: missing argument"
                if redir_stderr is not None:
                    if ensure_dir_exists(redir_stderr):
                        with open(redir_stderr, "w") as f:
                            f.write(error_msg + "\n")
                    else:
                        print(error_msg, file=sys.stderr)
                else:
                    print(error_msg, file=sys.stderr)
            else:
                path = parts[1]
                if path == "~":
                    home = os.environ.get("HOME")
                    if home:
                        path = home
                    else:
                        error_msg = "cd: HOME environment variable not set"
                        if redir_stderr is not None:
                            if ensure_dir_exists(redir_stderr):
                                with open(redir_stderr, "w") as f:
                                    f.write(error_msg + "\n")
                            else:
                                print(error_msg, file=sys.stderr)
                        else:
                            print(error_msg, file=sys.stderr)
                        continue
                if os.path.isdir(path):
                    os.chdir(path)
                else:
                    error_msg = f"cd: {path}: No such file or directory"
                    if redir_stderr is not None:
                        if ensure_dir_exists(redir_stderr):
                            with open(redir_stderr, "w") as f:
                                f.write(error_msg + "\n")
                        else:
                            print(error_msg, file=sys.stderr)
                    else:
                        print(error_msg, file=sys.stderr)
            continue

        if parts[0] == "type":
            if len(parts) < 2:
                error_msg = "type: missing argument"
                if redir_stderr is not None:
                    if ensure_dir_exists(redir_stderr):
                        with open(redir_stderr, "w") as f:
                            f.write(error_msg + "\n")
                    else:
                        print(error_msg, file=sys.stderr)
                else:
                    print(error_msg, file=sys.stderr)
                continue

            cmd = parts[1]
            if cmd in builtins:
                output = f"{cmd} is a shell builtin"
            else:
                path_env = os.environ.get("PATH", "")
                output = f"{cmd}: not found"
                for directory in path_env.split(":"):
                    file_path = os.path.join(directory, cmd)
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        output = f"{cmd} is {file_path}"
                        break

            if redir_stdout is not None:
                if ensure_dir_exists(redir_stdout):
                    with open(redir_stdout, "w") as f:
                        f.write(output + "\n")
                else:
                    print(output)
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
                    result = subprocess.run(new_args, executable=file_path,
                                            capture_output=True, text=True)

                    # Handle stdout redirection
                    if redir_stdout is not None:
                        if ensure_dir_exists(redir_stdout):
                            with open(redir_stdout, "w") as f:
                                f.write(result.stdout)
                        else:
                            if result.stdout:
                                print(result.stdout.strip())
                    else:
                        if result.stdout:
                            print(result.stdout.strip())

                    # Handle stderr redirection
                    if redir_stderr is not None:
                        if ensure_dir_exists(redir_stderr):
                            with open(redir_stderr, "w") as f:
                                f.write(result.stderr)
                        else:
                            if result.stderr:
                                print(result.stderr, file=sys.stderr, end="")
                    else:
                        if result.stderr:
                            print(result.stderr, file=sys.stderr, end="")

                    executed = True
                except Exception as e:
                    error_msg = f"Error executing {parts[0]}: {e}"
                    if redir_stderr is not None:
                        if ensure_dir_exists(redir_stderr):
                            with open(redir_stderr, "w") as f:
                                f.write(error_msg + "\n")
                        else:
                            print(error_msg, file=sys.stderr)
                    else:
                        print(error_msg, file=sys.stderr)
                break

        if not executed:
            error_msg = f"{' '.join(parts)}: command not found"
            if redir_stderr is not None:
                if ensure_dir_exists(redir_stderr):
                    with open(redir_stderr, "w") as f:
                        f.write(error_msg + "\n")
                else:
                    print(error_msg, file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)


if __name__ == "__main__":
    main()