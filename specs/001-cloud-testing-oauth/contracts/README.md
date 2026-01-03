# API Contracts: Cloud Testing Infrastructure with OAuth

**Feature**: 001-cloud-testing-oauth
**Date**: 2026-01-02

## Overview

This directory contains interface definitions (contracts) for the OAuth testing infrastructure. Since this is a Python library (not a REST/GraphQL API), contracts are defined as Python Protocol classes (PEP 544) and type stub interfaces.

These contracts serve as the specification for implementation and enable type checking with mypy/pyright.

---

## Contract Files

- **`credential_manager_protocol.py`** - Interface for credential loading and refreshing
- **`oauth_flow_protocol.py`** - Interface for OAuth authentication flows
- **`preflight_check_protocol.py`** - Interface for pre-flight credential validation
- **`google_api_client_protocol.py`** - Interface for Google API client wrappers
- **`test_resource_manager_protocol.py`** - Interface for test resource lifecycle management

---

## Type Safety Guarantees

All implementations must:
1. Pass `mypy --strict` type checking
2. Implement all methods defined in Protocol classes
3. Return types matching the interface specifications
4. Raise only exceptions documented in interface docstrings

---

## Testing Contracts

Contracts are validated through:
- **Static type checking**: `mypy` validates implementation conformance
- **Runtime protocol checking**: `isinstance(obj, ProtocolClass)` validates at runtime
- **Contract tests**: Test suites verify behavior matches specification
