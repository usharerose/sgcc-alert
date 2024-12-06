# sgcc-alert

![license](https://img.shields.io/github/license/usharerose/sgcc-alert)

Know your home power usage on time

## Development

### Environment

#### Docker (Recommended)
Execute the following commands, which sets up a service with development dependencies and enter into it.
```shell
> make run && make ssh
```

#### Virtual Environment
1. As a precondition, please [install Poetry](https://python-poetry.org/docs/1.7/#installation) which is a tool for dependency management and packaging in Python.
2. Install and activate local virtual environment
    ```shell
    > poetry install && poetry shell
    ```
3. `IPython` is provided as interactive shell
