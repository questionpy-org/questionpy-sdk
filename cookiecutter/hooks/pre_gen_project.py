import re
import sys

# TODO: Must not depend on questionpy packages... duplicate function here?
from questionpy_common.manifest import ensure_is_valid_name

short_name = "{{ cookiecutter.short_name }}"
namespace = "{{ cookiecutter.namespace }}"
languages = "{{ cookiecutter.languages }}"
iso_639_1_pattern = re.compile(r"^[a-z]{2}$", re.IGNORECASE)

# validate short name
try:
    ensure_is_valid_name(short_name)
except ValueError as err:
    print(f"ERROR: short_name '{short_name}' is not a valid Python module name! ({err})")
    sys.exit(-1)

# validate namespace
try:
    ensure_is_valid_name(namespace)
except ValueError as err:
    print(f"ERROR: namespace '{namespace}' is not a valid Python module name! ({err})")
    sys.exit(-1)

# validate language codes
for language in languages.split(","):
    # TODO: worth importing the whole list of valid languages?
    if not iso_639_1_pattern.match(language):
        print(f"ERROR: '{language}' is not a valid ISO 639-1 language code!")
        sys.exit(1)
