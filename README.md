# QuestionPy SDK

The toolset for developing and running `QuestionPy` packages.

## Setup

```shell
$ poetry install
```

## :package: Creating a QuestionPy Package

At minimum, a QuestionPy package requires a configuration file. The
configuration is a YAML-formatted file called `qpy_config.yml` at the root of
your package. See the `PackageConfig` and `SourceManifest` class for all supported
properties.

```yaml
# file example/qpy_config.yml

# A short, concise identifier for your package
short_name: example
# The current version of your package in the SemVer format
version: 0.1.0
# The minimum QuestionPy API version with which your package is compatible
api_version: 0.1
# You or your organization
author: Bob Sample <bob@example.org>
```

Once you have written your config, use the `package` command to create your
package as follows, where `example` is the directory in which your config
resides.

```shell
$ questionpy-sdk package example
```

If your package passes validation, you will have a new file called `example.qpy`. This is your question package,
ready for use.

### Including dependencies

You can specify the dependencies of your project in your config for the
QuestionPy SDK to automatically include them in the package.

```yaml
requirements:
  # List your dependencies here in any format understood by pip
  - numpy
  - requests==2.28.1
```

If you use a requirements.txt file, you can alternatively reference it to have its packages included.

```yaml
# Path relative to your qpy_config.yml
requirements: requirements.txt
```

## :rocket: Running a QuestionPy Package Locally

The SDK also executes question packages and provides their runtime.

```shell
$ questionpy-sdk run example.qpy
```
