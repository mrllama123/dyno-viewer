# AGENTS.md

This file provides guidance for agentic coding assistants working in this repository.

## Build, Lint, and Test Commands

### Installation

```bash
poetry install
```

### Running the Application

```bash
dyno-viewer  # Installed via poetry
poetry run dyno-viewer  # Run via poetry
```

### Linting

```bash
poe lint  # Runs all linters (pylint, black, isort)
poe check_black  # Check code formatting with black
poe check_imports  # Check import order with isort
poe pylint  # Run pylint

poe black  # Auto-format with black
poe isort  # Auto-sort imports with isort
poe lint-fix  # Run both black and isort to fix issues
```

### Testing

```bash
poe test  # Run all tests (uses pytest with xdist for parallel execution)
pytest -n auto  # Same as above (direct pytest command)
pytest tests/unit/foo/test_bar.py  # Run specific test file
pytest tests/unit/foo/test_bar.py::TestClass::test_method  # Run specific test
pytest -xvs  # Run tests with verbose output and stop on first failure
```

### Developer Tools

```bash
poe dev  # Run application in development mode with textual
poe dev-server  # Run application as a server in development mode
poe dev-console  # Run textual console
```

## Code Style Guidelines

### Python Version
- Python 3.10+ required
- Type annotations required (PEP 484)

### Imports
- Imports grouped by standard library, third-party, local
- Absolute imports only (no relative imports)
- Imports sorted alphabetically within groups using `isort` with black profile
- No implicit relative imports (e.g., `from . import foo`)

```python
# Good
import os
import logging

import boto3
from textual import on
from pydantic import BaseModel

from dyno_viewer.models import QueryParameters
from dyno_viewer.aws.ddb import get_table
```

### Formatting
- Line length: 88 characters (black default)
- Use `black` for code formatting
- Use `isort` for import sorting (profile=black)

### Type Hints
- Use type hints consistently (PEP 484)
- Use `TypedDict` for dictionary types with known keys
- Use `dataclasses` or `pydantic.BaseModel` for structured data
- Prefer `dict[str, str]` over `Dict[str, str]` (PEP 604)
- For optional types, use `str | None` instead of `Optional[str]`

```python
# Good
from typing import TypedDict

class TableInfo(TypedDict):
    tableName: str = ""
    keySchema: dict[str, str]
```

```python
# Good
async def get_item(table_name: str) -> dict | None:
    ...
```

### Naming Conventions
- `snake_case` for variables, functions, and methods
- `CamelCase` for classes and class methods
- `UPPER_CASE` for constants
- `lower_case` for module-level variables
- Use descriptive names, avoid abbreviations where clarity is lost

### Error Handling
- Use specific exceptions rather than bare `except:`
- Handle exceptions at the appropriate level
- Use `log.error()` for logging errors
- Provide meaningful error messages
- Avoid silent failures

```python
# Good
def get_table(table_name: str) -> Any:
    try:
        return get_table_client(table_name)
    except Exception as error:
        if error.response["Error"]["Code"] in [
            "ResourceNotFoundException",
        ]:
            return None
        raise error
```

### Strings
- Use f-strings for string formatting
- Use `simplejson` for JSON serialization/deserialization (handles Decimal)

### Constants
- Define constants at the module level
- Use `UPPER_CASE` naming for constants

```python
LOG_LEVEL = logging.INFO
ATTRIBUTE_TYPES = ["string", "number", "boolean", "set", "map", "list"]
```

### Classes and Methods
- Use `BaseModel` from `pydantic` for data validation
- Implement `@property` for derived attributes
- Use `@computed_field` for computed fields in Pydantic models
- Use type hints for all method parameters and return types

```python
class QueryParameters(BaseModel):
    scan_mode: bool = False
    primary_key_name: str
    sort_key_name: str
    index: str = "table"

    @computed_field
    @property
    def boto_params(self) -> dict:
        params = {} if self.scan_mode else {"KeyConditionExpression": self._boto_key_condition()}
        if self.filter_conditions:
            params["FilterExpression"] = self._boto_filter_condition()
        return params
```

### Database Operations
- Use async/await for database operations
- Use `aiosqlite` for SQLite operations
- Use SQLAlchemy or similar ORM for complex queries
- Handle connection errors and retries appropriately

### Logging
- Use appropriate log levels: `INFO`, `WARNING`, `ERROR`, `DEBUG`
- Log meaningful context with errors
- Avoid logging sensitive data

```python
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.info("Batch reading %s item keys.", len(keys))
logger.error("Connection error: %s", error, exc_info=True)
```

### Async Code
- Use `async def` for coroutines
- Use `@work` decorator for background tasks in Textual
- Use proper error handling with try/except
- Set `exclusive=True` when operations should not overlap

```python
@work(exclusive=True, group="on_mount_setup")
async def on_mount_setup(self) -> None:
    self.dyn_client = get_ddb_client(
        region_name=self.aws_region, profile_name=self.aws_profile
    )
```

### Tests
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use `pytest` for test discovery
- Use `moto` for mocking AWS services
- Test edge cases and error conditions
- Keep tests focused and independent

```python
def test_get_item(mocker, test_table):
    # Arrange
    ddb_client = get_table_client(test_table)
    
    # Act
    result = get_item(test_table, {"pk": "test", "sk": "test"})
    
    # Assert
    assert result is not None
```

## Code Organization

### Directory Structure
```
project/
├── dyno_viewer/         # Main application code
│   ├── __main__.py      # Entry point
│   ├── app.py           # Main application class
│   ├── models.py        # Pydantic models
│   ├── aws/             # AWS-related code
│   ├── components/      # Textual components
│   ├── db/              # Database operations
│   └── util/            # Utility functions
├── tests/               # Tests
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
└── scripts/             # Utility scripts
```

### Files
- Keep files focused on a single responsibility
- Order methods by type: public, private (use single underscore prefix)
- Order classes by dependency (base classes first)
- Use `__all__` to control public API when needed

## AWS/DynamoDB Best Practices

### Querying
- Use key conditions for efficient queries
- Use filter expressions for post-query filtering
- Limit results with `Limit` parameter when appropriate
- Use pagination for large result sets

### Error Handling
- Handle `ResourceNotFoundException` when checking for tables
- Handle `ValidationException` for invalid queries
- Handle throttling errors with retries

### Client Initialization
- Initialize boto3 clients/resources once and reuse
- Use session profiles when available

```python
def get_ddb_client(region_name="ap-southeast-2", profile_name=None):
    return (
        Session(profile_name=profile_name, region_name=region_name).client("dynamodb")
        if profile_name
        else boto3.client("dynamodb", region_name=region_name)
    )
```

## Textual-Specific Guidelines

### Components
- Use `reactive` for state management
- Use `@on` decorator for message handling
- Use `@watch` for reactive property changes
- Use `@work` for background tasks

### Messages
- Create custom messages for component communication
- Use `Message` base class
- Keep messages simple and focused

```python
class QueryResult(Message):
    def __init__(self, data, next_token, update_existing_data=False) -> None:
        self.data = data
        self.next_token = next_token
        self.update_existing_data = update_existing_data
        super().__init__()
```

### Screens
- Use screens for modal dialogs and workflows
- Use `Screen` base class for full-screen views
- Use `push_screen()` for navigation
- Use `push_screen_wait()` for blocking dialogs

### Bindings
- Define key bindings in `BINDINGS` class attribute
- Use descriptive names for actions
- Document available bindings with `HELP` attribute

```python
BINDINGS = [
    Binding("t", "select_table", "Select table", show=False),
    Binding("q", "query_table", "Query table", show=False),
]
```

## Git Workflow

### Branching
- Use feature branches for new functionality
- Use descriptive branch names: `feature/add-xyz`
- Keep branches focused (single responsibility)

### Committing
- Write descriptive commit messages
- Follow conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Reference issues with `#issue-number` when applicable

### Pull Requests
- Include description of changes
- Reference related issues
- Add screenshots for UI changes
- Request reviews from team members

## Documentation

### Python Docs
- Add docstrings to public functions and classes
- Use Google style docstrings
- Document parameters and return types

```python
def query_items(table, paginate=True, **query_kwargs):
    """
    Query items from a DynamoDB table.
    
    :param table: name or client of the dynamodb table
    :param paginate: whether to paginate through results
    :param query_kwargs: additional parameters for the query
    :return: list of items or paginated results
    """
```

### Code Comments
- Use comments sparingly
- Prefer clear code over comments
- Use comments to explain **why** not **what**
- Avoid redundant comments

### Inline Comments
- Use `# ` for single-line comments
- Place comments on the line above the code they reference
- Use `""""` for multi-line comments

## CI/CD

### GitHub Actions
- `.github/workflows/pr-tests.yml` runs on PR to master
- Runs unit tests with `poe test`
- Runs linting with `poe lint`

### Environments
- `master` branch is protected
- Requires PR for changes
- Requires successful CI checks

## Python-Specific Tools

### Poetry
- Dependency management
- Virtual environments
- Packaging

```bash
poetry add package  # Add dependency
poetry remove package  # Remove dependency
poetry lock  # Update lock file
```

### Pylint
- Configured via `pyproject.toml`
- Many checks disabled (listed in config)
- Focus on code clarity and maintainability

### Black
- Line length: 88
- Python version target: py38
- Auto-formatting tool

## Additional Notes

### Decimal Handling
- Use `Decimal` for numerical values from DynamoDB
- Use `simplejson` for JSON serialization (handles Decimal)

### Logging
- Use `textual.log` for application logging
- Use standard `logging` module for other uses

### Configuration
- Use `pyproject.toml` for project configuration
- Use `CONFIG_DIR_NAME` and related constants for app-specific paths

### Testing with Textual
- Use snapshots for UI testing
- Test key bindings and message flows
