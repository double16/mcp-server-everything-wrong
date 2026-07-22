# AGENTS.md

## Project overview

This repository is an intentionally insecure Model Context Protocol (MCP) server used to demonstrate malicious and unsafe tool behaviors. Many suspicious implementations in `src/mcp_server_everything_wrong/server.py` are deliberate examples, not accidental defects. Do not sanitize, remove, or make those demonstrations safe unless the task explicitly asks for that behavior change.

The server supports two deployment modes backed by the same ASGI application:

- Stand-alone HTTP server through the `mcp-server-everything-wrong` console script.
- AWS Lambda through `mcp_server_everything_wrong.aws_lambda.lambda_handler`, using Mangum as a thin adapter.

## Repository layout

- `src/mcp_server_everything_wrong/server.py`: MCP tools, API-key middleware, shared ASGI app factory, and stand-alone Uvicorn startup.
- `src/mcp_server_everything_wrong/aws_lambda.py`: AWS Lambda/Mangum wrapper. Keep MCP behavior out of this module.
- `src/mcp_server_everything_wrong/__init__.py`: console-script entry point.
- `tests/test_server.py`: API-key middleware and stand-alone server tests.
- `tests/test_aws_lambda.py`: Lambda adapter delegation test.
- `README.md`: usage, deployment instructions, and descriptions of the intentionally unsafe tools.
- `pyproject.toml`: Python requirements, runtime dependencies, and development tools.
- `uv.lock`: locked dependency graph; update it when dependencies change.

## Development commands

Use `uv` for dependency management and command execution. The project requires Python 3.12 or newer.

```console
uv run python -m unittest discover -s tests -v
uv run --extra dev ruff check .
uv run --extra dev pyright src tests
```

When changing dependencies, regenerate the lockfile:

```console
uv lock
```

Run the stand-alone server with:

```console
uv run mcp-server-everything-wrong
```

It listens on `http://0.0.0.0:8000`, with MCP requests under `/mcp`.

## Architecture and implementation rules

- Keep `create_app()` as the single source of the ASGI application used by both deployment modes.
- Keep the Lambda function as a thin wrapper around that application; do not duplicate middleware, MCP registration, or business logic in `aws_lambda.py`.
- `serve()` is asynchronous and must await Uvicorn's `Server.serve()`.
- `MCP_API_KEY` is optional. When set, it protects `/mcp` requests and accepts either the raw key or `Bearer <key>` in the `Authorization` header.
- Read `MCP_API_KEY` at request time so environment updates are honored without rebuilding the application.
- Never log authorization headers, API keys, or other credentials. Preserve constant-time key comparison with `hmac.compare_digest`.
- Do not broaden API-key protection to unrelated paths without an explicit requirement.
- Preserve Python 3.12-compatible type annotations and the existing source-file license headers.

## Testing expectations

- For middleware changes, cover configured and unconfigured keys, missing and invalid authorization, raw and bearer formats, and non-MCP paths.
- For stand-alone startup changes, verify the Uvicorn configuration and that the asynchronous server method is awaited.
- For Lambda changes, verify that the event and context are delegated unchanged to the adapter.
- Run the unit tests, Ruff, and Pyright after code changes. Do not consider the task complete with failing tests, lint errors, or type errors.
- Documentation-only changes do not require running the test suite unless they alter executable examples or commands.

## Documentation guidance

- Keep the README's strong warning that this server is intentionally unsafe and unsuitable for production.
- When adding or changing an intentionally malicious tool, document its behavior in the available-tools table and relevant usage section.
- Keep stand-alone and Lambda deployment instructions aligned when shared server behavior changes.
- Clearly distinguish intentional vulnerabilities from deployment and authentication code, which should remain production-quality within the demonstration's scope.