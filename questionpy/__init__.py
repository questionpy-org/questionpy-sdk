# This is a pkgutil-style namespace package, because PyLint does not support PEP 420 native namespace packages :(
# https://packaging.python.org/en/latest/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages
# https://github.com/PyCQA/pylint/issues/2862
__path__ = __import__('pkgutil').extend_path(__path__, __name__)
