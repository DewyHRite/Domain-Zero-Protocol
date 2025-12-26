# pytest Complete Guide
<!-- Domain Zero Protocol v8.10.0 - Offline Reference -->

**Agent**: Yuuji (Implementation Specialist)
**Last Updated**: 2025-12-26
**Source**: [pytest Documentation](https://docs.pytest.org/)

---

## Table of Contents

1. [Installation](#installation)
2. [Writing Tests](#writing-tests)
3. [Fixtures](#fixtures)
4. [Markers](#markers)
5. [Parametrization](#parametrization)
6. [Assertions](#assertions)
7. [Mocking](#mocking)
8. [Async Testing](#async-testing)
9. [Configuration](#configuration)
10. [Best Practices](#best-practices)

---

## Installation

```bash
# Install pytest
pip install -U pytest

# Verify installation
pytest --version

# Install common plugins
pip install pytest-cov pytest-asyncio pytest-mock pytest-xdist
```

---

## Writing Tests

### Basic Test Structure

pytest discovers tests automatically in files matching `test_*.py` or `*_test.py`.

```python
# test_sample.py
def func(x):
    return x + 1

def test_answer():
    assert func(3) == 4

def test_negative():
    assert func(-1) == 0
```

### Class-Based Tests

Group related tests using classes prefixed with `Test`:

```python
class TestCalculator:
    def test_add(self):
        assert 1 + 1 == 2

    def test_subtract(self):
        assert 5 - 3 == 2

    def test_multiply(self):
        assert 3 * 4 == 12
```

**Important**: Each test receives its own class instance, preventing shared state issues.

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest test_sample.py

# Run specific test
pytest test_sample.py::test_answer

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=mypackage

# Run in parallel
pytest -n auto  # requires pytest-xdist
```

---

## Fixtures

Fixtures provide reusable test resources and setup/teardown logic.

### Basic Fixture

```python
import pytest

@pytest.fixture
def sample_data():
    return {"name": "test", "value": 42}

def test_with_data(sample_data):
    assert sample_data["name"] == "test"
    assert sample_data["value"] == 42
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - runs per test
def func_fixture():
    return "function"

@pytest.fixture(scope="class")  # Runs once per test class
def class_fixture():
    return "class"

@pytest.fixture(scope="module")  # Runs once per module
def module_fixture():
    return "module"

@pytest.fixture(scope="session")  # Runs once per test session
def session_fixture():
    return "session"
```

### Setup and Teardown

```python
@pytest.fixture
def database_connection():
    # Setup
    conn = create_connection()
    yield conn  # Provide the fixture value
    # Teardown (runs after test)
    conn.close()

def test_database_query(database_connection):
    result = database_connection.query("SELECT 1")
    assert result == 1
```

### Built-in Fixtures

```python
def test_temp_files(tmp_path):
    """tmp_path provides a temporary directory."""
    file = tmp_path / "test.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"

def test_capture_output(capsys):
    """capsys captures stdout/stderr."""
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"

def test_monkeypatch(monkeypatch):
    """monkeypatch modifies objects during tests."""
    monkeypatch.setenv("API_KEY", "test-key")
    import os
    assert os.environ["API_KEY"] == "test-key"
```

---

## Markers

Markers add metadata to tests for filtering and configuration.

### Built-in Markers

```python
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_skip():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_conditional_skip():
    pass

@pytest.mark.xfail(reason="Known bug in library")
def test_expected_failure():
    assert False  # Won't cause test failure

@pytest.mark.slow
def test_slow_operation():
    # Custom marker - run with: pytest -m slow
    pass
```

### Register Custom Markers

```ini
# pytest.ini or pyproject.toml
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Running Marked Tests

```bash
# Run only slow tests
pytest -m slow

# Run everything except slow tests
pytest -m "not slow"

# Run unit OR integration tests
pytest -m "unit or integration"
```

---

## Parametrization

Run tests with multiple input sets.

### Basic Parametrization

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
    (3, 4),
    (-1, 0),
])
def test_increment(input, expected):
    assert input + 1 == expected
```

### Multiple Parameters

```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    # Runs 6 tests: (1,10), (1,20), (2,10), (2,20), (3,10), (3,20)
    assert x * y > 0
```

### Parametrized Fixtures

```python
@pytest.fixture(params=["mysql", "postgres", "sqlite"])
def database(request):
    db_type = request.param
    return create_database(db_type)

def test_database_operations(database):
    # Runs 3 times, once for each database type
    assert database.connect()
```

---

## Assertions

### Basic Assertions

```python
def test_assertions():
    # Equality
    assert 1 + 1 == 2

    # Truthiness
    assert True
    assert not False

    # Membership
    assert "a" in "abc"
    assert 1 in [1, 2, 3]

    # Identity
    assert [] is not []

    # Comparison
    assert 5 > 3
    assert 3 <= 3
```

### Exception Testing

```python
import pytest

def test_raises_exception():
    with pytest.raises(ValueError):
        raise ValueError("invalid value")

def test_exception_message():
    with pytest.raises(ValueError, match="invalid"):
        raise ValueError("invalid value")

def test_exception_details():
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("test error")
    assert "test" in str(exc_info.value)
```

### Floating-Point Comparison

```python
def test_floating_point():
    # Avoid floating point comparison issues
    assert (0.1 + 0.2) == pytest.approx(0.3)

    # With tolerance
    assert 2.0 == pytest.approx(2.01, abs=0.1)
    assert 100 == pytest.approx(101, rel=0.02)  # 2% tolerance
```

---

## Mocking

### Using pytest-mock

```python
def test_mock_function(mocker):
    # Mock a function
    mock_api = mocker.patch("mymodule.api_call")
    mock_api.return_value = {"status": "ok"}

    result = mymodule.process_data()

    mock_api.assert_called_once()
    assert result["status"] == "ok"
```

### Using monkeypatch

```python
def test_monkeypatch_attribute(monkeypatch):
    # Replace attribute
    monkeypatch.setattr("os.getcwd", lambda: "/fake/path")

    import os
    assert os.getcwd() == "/fake/path"

def test_monkeypatch_dict(monkeypatch):
    # Modify dictionary
    config = {"debug": False}
    monkeypatch.setitem(config, "debug", True)
    assert config["debug"] == True
```

### Mock Classes

```python
from unittest.mock import MagicMock, patch

def test_mock_class():
    mock_db = MagicMock()
    mock_db.query.return_value = [{"id": 1}]

    result = mock_db.query("SELECT * FROM users")

    assert len(result) == 1
    mock_db.query.assert_called_with("SELECT * FROM users")
```

---

## Async Testing

Requires `pytest-asyncio` plugin.

```bash
pip install pytest-asyncio
```

### Basic Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_fetch_data()
    assert result is not None

@pytest.mark.asyncio
async def test_async_with_timeout():
    import asyncio
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(), timeout=0.1)
```

### Async Fixtures

```python
@pytest.fixture
async def async_database():
    db = await create_async_connection()
    yield db
    await db.close()

@pytest.mark.asyncio
async def test_async_query(async_database):
    result = await async_database.fetch("SELECT 1")
    assert result == 1
```

### Configure Async Mode

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

---

## Configuration

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
markers = [
    "slow: marks tests as slow",
    "integration: integration tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]
```

### pytest.ini

```ini
[pytest]
minversion = 7.0
addopts = -ra -q
testpaths = tests
markers =
    slow: marks tests as slow
    integration: integration tests
```

### conftest.py

Shared fixtures and hooks for all tests in directory:

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    return create_app(testing=True)

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def pytest_configure(config):
    """Custom pytest configuration."""
    config.addinivalue_line("markers", "e2e: end-to-end tests")
```

---

## Best Practices

### 1. Test Organization

```
project/
    src/
        mypackage/
            __init__.py
            module.py
    tests/
        __init__.py
        conftest.py
        unit/
            test_module.py
        integration/
            test_api.py
```

### 2. Naming Conventions

```python
# Test files: test_*.py or *_test.py
# Test functions: test_*
# Test classes: Test*

def test_user_creation_with_valid_email():
    """Descriptive names explain what is being tested."""
    pass

def test_login_fails_with_invalid_credentials():
    """Include expected outcome in name."""
    pass
```

### 3. AAA Pattern (Arrange-Act-Assert)

```python
def test_user_full_name():
    # Arrange
    user = User(first_name="John", last_name="Doe")

    # Act
    full_name = user.get_full_name()

    # Assert
    assert full_name == "John Doe"
```

### 4. One Assertion Per Test (When Possible)

```python
# Good - focused tests
def test_user_has_correct_first_name():
    user = User(first_name="John")
    assert user.first_name == "John"

def test_user_has_correct_last_name():
    user = User(last_name="Doe")
    assert user.last_name == "Doe"

# Acceptable - related assertions
def test_user_creation():
    user = User(first_name="John", last_name="Doe")
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.full_name == "John Doe"
```

### 5. Use Fixtures for Repeated Setup

```python
# Bad - repeated setup
def test_one():
    db = create_database()
    user = db.create_user("test")
    # test logic

def test_two():
    db = create_database()
    user = db.create_user("test")
    # test logic

# Good - use fixtures
@pytest.fixture
def user(db):
    return db.create_user("test")

def test_one(user):
    # test logic

def test_two(user):
    # test logic
```

### 6. Test Edge Cases

```python
@pytest.mark.parametrize("input,expected", [
    ("", ""),           # Empty string
    ("a", "A"),         # Single character
    ("hello", "Hello"), # Normal case
    ("HELLO", "Hello"), # Already uppercase
    ("123", "123"),     # Numbers
    (None, None),       # None handling
])
def test_capitalize(input, expected):
    assert capitalize(input) == expected
```

### 7. Avoid Test Interdependence

```python
# Bad - tests depend on each other
class TestUserFlow:
    user_id = None

    def test_create_user(self):
        TestUserFlow.user_id = create_user()

    def test_get_user(self):
        get_user(TestUserFlow.user_id)  # Depends on test_create_user

# Good - each test is independent
def test_create_and_get_user():
    user_id = create_user()
    user = get_user(user_id)
    assert user is not None
```

---

## Quick Reference

### Common Commands

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -x                       # Stop on first failure
pytest --lf                     # Run last failed tests
pytest -k "keyword"             # Run tests matching keyword
pytest -m "marker"              # Run tests with marker
pytest --cov=package            # Run with coverage
pytest -n auto                  # Run in parallel
pytest --durations=10           # Show 10 slowest tests
```

### Common Assertions

```python
assert x == y                   # Equality
assert x != y                   # Inequality
assert x is None                # None check
assert x is not None            # Not None
assert x in collection          # Membership
assert isinstance(x, Type)      # Type check
pytest.raises(Exception)        # Exception
pytest.approx(x)               # Float comparison
```

---

**Online Reference**: [pytest Documentation](https://docs.pytest.org/)
