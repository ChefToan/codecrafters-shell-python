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
                    redir_stdout = tokens[i+1]
                    i += 2
                    continue
                else:
                    err = "Error: No file specified for redirection"
                    if redir_stderr:
                        with open(redir_stderr, "w") as f:
                            f.write(err + "\n")
                    else:
                        print(err)
                    break
            elif token == "2>":
                if i + 1 < len(tokens):
                    redir_stderr = tokens[i+1]
                    i += 2
                    continue
                else:
                    err = "Error: No file specified for redirection"
                    if redir_stderr:
                        with open(redir_stderr, "w") as f:
                            f.write(err + "\n")
                    else:
                        print(err)
                    break
            else:
                new_parts.append(token)
                i += 1

        if not new_parts:
            continue

        parts = new_parts

        # Helper functions to write output/errors based on redirections
        def output_result(output):
            if redir_stdout is not None:
                with open(redir_stdout, "w") as f:
                    f.write(output + "\n")
            elif redir_stderr is not None:
                with open(redir_stderr, "w") as f:
                    f.write(output + "\n")
            else:
                print(output)

        def output_error(error):
            if redir_stderr is not None:
                with open(redir_stderr, "w") as f:
                    f.write(error + "\n")
            else:
                sys.stderr.write(error + "\n")

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
            output_result(output)
            continue

        if parts[0] == "pwd":
            output = os.getcwd()
            output_result(output)
            continue

        if parts[0] == "cd":
            if len(parts) < 2:
                output_error("cd: missing argument")
            else:
                path = parts[1]
                if path == "~":
                    home = os.environ.get("HOME")
                    if home:
                        path = home
                    else:
                        output_error("cd: HOME environment variable not set")
                        continue
                if os.path.isdir(path):
                    os.chdir(path)
                else:
                    output_error(f"cd: {path}: No such file or directory")
            continue

        if parts[0] == "type":
            if len(parts) < 2:
                output_error("type: missing argument")
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
            output_result(output)
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
                    if redir_stdout is not None:
                        with open(redir_stdout, "w") as f:
                            f.write(result.stdout)
                    else:
                        if result.stdout:
                            print(result.stdout.strip())
                    if redir_stderr is not None:
                        with open(redir_stderr, "w") as f:
                            f.write(result.stderr)
                    else:
                        if result.stderr:
                            sys.stderr.write(result.stderr)
                    executed = True
                except Exception as e:
                    output_error(f"Error executing {parts[0]}: {e}")
                break

        if not executed:
            output_error(f"{' '.join(parts)}: command not found")

if __name__ == "__main__":
    main()