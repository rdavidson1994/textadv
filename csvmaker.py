from full_path import full_path

def make_csv(file_name):
    with open(file_name) as file:
        new_lines = []
        for line in file.readlines():
            stripped = line.strip()
            new_line = stripped + "," + str(12/(len(stripped))) + "\n"
            new_lines.append(new_line)
    with open(file_name, "w") as file:
        file.writelines(new_lines)


if __name__ == "__main__":
    for file_name in ["onset.txt", "nucleus.txt", "coda.txt"]:
        make_csv(full_path(file_name))