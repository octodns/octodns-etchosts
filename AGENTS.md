# Developer Agent Guide for octoDNS EtcHosts Provider

This repository contains the EtcHosts provider for octoDNS. It writes local `/etc/hosts`-compatible files mapping DNS zone records to their resolved IP addresses.

> [!IMPORTANT]
> **Core Workflow and Guidelines**
>
> All agents working on this repository must read and follow the general instructions and workflow guidelines defined in the core octoDNS `AGENTS.md` file.
> - **Local check**: Look for the file at `../octodns/AGENTS.md`.
> - **Remote check**: If the local file is not available, fetch it from GitHub: [octoDNS Core AGENTS.md](https://github.com/octodns/octodns/raw/refs/heads/main/AGENTS.md).
>
> You must align your code structure, style, pull request guidelines, and overall development workflows with the instructions specified there.

## Repository & Module Information

### Key Components

- **Provider Class**: [EtcHostsProvider](file:///home/ross/octodns/octodns-etchosts/octodns_etchosts/__init__.py#L24-L190) (defined in [octodns_etchosts/__init__.py](file:///home/ross/octodns/octodns-etchosts/octodns_etchosts/__init__.py)). This is the core provider implementing host file writing, alias resolution, and wildcard matching.

### Key Workflows & Features

1. **Supported Record Types**: `A`, `AAAA`, `ALIAS`, `CNAME`.
2. **CNAME/ALIAS Chain Chasing**: The provider chases alias and CNAME targets recursively to extract physical leaf IP addresses (`A` or `AAAA` values) for hosts file records. It implements loop checks using a traversal stack.
3. **Wildcard Resolution**: Implements wildcard matchers (`_wildcard_match`) to resolve dynamic subdomain paths.
4. **Hosts Formatting**: Writes standard hosts entries to target files named `<zone-name>hosts` under the configured `directory`. Supports removing trailing dots (`remove_trailing_dots=True`) to conform to hostfile syntax.
5. **Dynamic Routing**: Not supported (`SUPPORTS_DYNAMIC=False`, `SUPPORTS_GEO=False`).
6. **Dynamic Subnets**: Not supported (`SUPPORTS_DYNAMIC_SUBNETS=False`).
7. **Pool Value Status**: Not supported (`SUPPORTS_POOL_VALUE_STATUS=False`).

## Development & Testing

- **Setup Script**: Run `./script/bootstrap` to create a virtual environment, install dependencies (including `black`, `isort`, `pyflakes`, and `pytest`), and configure pre-commit hooks.
- **Test Suite**: Run unit tests using `pytest` via `./script/test` (or `pytest tests/`). Test files are located in [tests/](file:///home/ross/octodns/octodns-etchosts/tests).
- **Code Coverage**: Verify code coverage using `./script/coverage`.

## Key Constraints & Behaviors

- **Python Version**: Targets Python `>=3.9`.
- **Formatting**: Code formatting is enforced via `black` (version `>=26.0.0,<27.0.0`) and `isort`.
