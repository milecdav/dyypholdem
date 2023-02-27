def log_line(line: str, file_name):
    """Log a line to a file."""
    with open(file_name, 'a') as file:
        file.write("./" + line + "\n")
