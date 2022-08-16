# QuestionPy SDK

The toolset for developing and running `QuestionPy` packages.

## Setup

```shell
$ poetry install
```

## :package: Creating a QuestionPy Package

At minimum, a QuestionPy package requires a manifest. The manifest is a YAML-formatted file called `qpy_manifest.yml` at
the root of your package. See the [Manifest](questionpy/_manifest.py) class for all supported properties.

```yaml
# file example/qpy_manifest.yml

# A short, concise identifier for your package
short_name: example
# The current version of your package in the SemVer format
version: 0.1.0
# The minimum QuestionPy API version with which your package is compatible
api_version: 0.1
# You or your organization
author: Bob Sample <bob@example.org>
# Optional: The module within your package which should be imported when the package is run
entrypoint: main
```

Once you have written your manifest, use the `package` command to create your package as follows, where `example` is
the directory in which your manifest resides.

```shell
$ python -m questionpy_sdk package example
```

If your package passes validation, you will have a new file called `example.qpy`. This is your question package,
ready for use.

### Including dependencies

You can specify the dependencies of your project in your manifest for the QuestionPy SDK to automatically include them
in the package.

```yaml
requirements:
  # List your dependencies here in any format understood by pip
  - numpy
  - requests==2.28.1
```

If you use a requirements.txt file, you can alternatively reference it to have its packages included.

```yaml
# Path relative to your qpy_manifest.yml
requirements: requirements.txt
```

## :rocket: Running a QuestionPy Package Locally

The SDK also executes question packages and provides their runtime.

```shell
$ python -m questionpy_sdk run example.qpy
```

You can then communicate with the question package using JSON objects on stdin and stdout, although it is often more
comfortable to pipe in messages on the command line.

```shell
$ echo '{"kind": "ping"}' | python -m questionpy_sdk run example.qpy
{"kind": "pong"}
```

The flag `--pretty`/`-p` will cause responses to be indented over multiple lines.
