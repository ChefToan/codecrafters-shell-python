import os
import sys
import subprocess
import shlex
import readline


# Track completion state
_last_text = None
_tab_count = 0
_all_matches = []


def find_longest_common_prefix(strings):
    """Find the longest common prefix of a list of strings"""
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]

    prefix = ""
    for i in range(min(len(s) for s in strings)):
        char = strings[0][i]
        if all(s[i] == char for s in strings):
            prefix += char
        else:
            break
    return prefix


def completer(text, state):
    """Provide tab completion for builtin commands and executables in PATH"""
    global _last_text, _tab_count, _all_matches

    # Reset counter if text changed
    if text != _last_text:
        _last_text = text
        _tab_count = 0
        _all_matches = []

    # Increment tab count
    if state == 0:
        _tab_count += 1

    # Get matching commands
    if state == 0 or not _all_matches:
        builtins = ["echo", "exit", "type", "pwd", "cd"]
        matches = [cmd for cmd in builtins if cmd.startswith(text)]

        # Add executables from PATH
        path_env = os.environ.get("PATH", "")
        for directory in path_env.split(":"):
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        filepath = os.path.join(directory, filename)
                        if os.path.isfile(filepath) and os.access(filepath, os.X_OK) and filename.startswith(text):
                            if filename not in matches:
                                matches.append(filename)
                except OSError:
                    continue

        _all_matches = sorted(matches)

    # No matches
    if not _all_matches:
        return None

    # Single match
    if len(_all_matches) == 1:
        return _all_matches[0] + " " if state == 0 else None

    # Multiple matches
    common_prefix = find_longest_common_prefix(_all_matches)

    # If common prefix is longer than what user typed, return it
    if len(common_prefix) > len(text):
        return common_prefix if state == 0 else None

    # If on first tab and no better completion available
    if _tab_count == 1:
        sys.stdout.write('\a')
        sys.stdout.flush()
        return text if state == 0 else None

    # On second tab, show all matches
    if _tab_count >= 2 and state == 0:
        print()
        print("  ".join(_all_matches))
        print(f"$ {text}", end="")
        return None

    # Return specific match if state is valid
    return _all_matches[state] if state < len(_all_matches) else None


def main():
    # Set up tab completion
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

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

        redir_stdout = None
        redir_stderr = None
        append_stdout = False
        append_stderr = False
        new_parts = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token in (">", "1>"):
                if i + 1 < len(tokens):
                    redir_stdout = tokens[i + 1]
                    append_stdout = False
                    i += 2
                    continue
                else:
                    print("Error: No file specified for redirection")
                    break
            elif token in (">>", "1>>"):
                if i + 1 < len(tokens):
                    redir_stdout = tokens[i + 1]
                    append_stdout = True
                    i += 2
                    continue
                else:
                    print("Error: No file specified for redirection")
                    break
            elif token == "2>":
                if i + 1 < len(tokens):
                    redir_stderr = tokens[i + 1]
                    append_stderr = False
                    i += 2
                    continue
                else:
                    print("Error: No file specified for redirection")
                    break
            elif token == "2>>":
                if i + 1 < len(tokens):
                    redir_stderr = tokens[i + 1]
                    append_stderr = True
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

            if redir_stderr is not None:
                ensure_dir_exists(redir_stderr)
                mode = 'a' if append_stderr else 'w'
                with open(redir_stderr, mode) as f:
                    pass

            if redir_stdout is not None:
                if ensure_dir_exists(redir_stdout):
                    mode = 'a' if append_stdout else 'w'
                    with open(redir_stdout, mode) as f:
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
                    mode = 'a' if append_stdout else 'w'
                    with open(redir_stdout, mode) as f:
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
                        mode = 'a' if append_stderr else 'w'
                        with open(redir_stderr, mode) as f:
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
                                mode = 'a' if append_stderr else 'w'
                                with open(redir_stderr, mode) as f:
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
                            mode = 'a' if append_stderr else 'w'
                            with open(redir_stderr, mode) as f:
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
                        mode = 'a' if append_stderr else 'w'
                        with open(redir_stderr, mode) as f:
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
                    mode = 'a' if append_stdout else 'w'
                    with open(redir_stdout, mode) as f:
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
                            mode = 'a' if append_stdout else 'w'
                            with open(redir_stdout, mode) as f:
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
                            mode = 'a' if append_stderr else 'w'
                            with open(redir_stderr, mode) as f:
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
                            mode = 'a' if append_stderr else 'w'
                            with open(redir_stderr, mode) as f:
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
                    mode = 'a' if append_stderr else 'w'
                    with open(redir_stderr, mode) as f:
                        f.write(error_msg + "\n")
                else:
                    print(error_msg, file=sys.stderr)
            else:
                print(error_msg, file=sys.stderr)


if __name__ == "__main__":
    main()