
def sort_file_and_dedupe(filename: str) -> str:
    with open(filename, "w+") as file:
        namelist = file.readlines()
        name_set = set()
        for name in namelist:
            _name = name.strip().lower()
            if _name:
                name_set.add(_name)
        file.seek(0)
        sorted_names = sorted(name_set)
        for _name in sorted_names:
            file.write(f"{_name}\n")