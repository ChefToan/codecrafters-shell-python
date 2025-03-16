import sys

def main():
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

        print(f"{command}: command not found")

if __name__ == "__main__":
    main()
