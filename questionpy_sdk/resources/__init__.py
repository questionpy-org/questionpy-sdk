from importlib.resources import as_file, files


with as_file(files(__package__)) as directory:
    EXAMPLE_PACKAGE = directory / "example.zip"
