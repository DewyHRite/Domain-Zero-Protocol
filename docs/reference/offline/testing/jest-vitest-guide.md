# Jest & Vitest Testing Guide
<!-- Domain Zero Protocol v8.10.0 - Offline Reference -->

**Agent**: Yuuji (Implementation Specialist)
**Last Updated**: 2025-12-26
**Sources**: [Jest](https://jestjs.io/), [Vitest](https://vitest.dev/)

---

## Table of Contents

1. [Installation](#installation)
2. [Writing Tests](#writing-tests)
3. [Matchers](#matchers)
4. [Mocking](#mocking)
5. [Async Testing](#async-testing)
6. [Snapshots](#snapshots)
7. [Configuration](#configuration)
8. [Testing Library Integration](#testing-library-integration)
9. [Best Practices](#best-practices)

---

## Installation

### Jest

```bash
# npm
npm install --save-dev jest

# With TypeScript
npm install --save-dev jest ts-jest @types/jest

# Add to package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

### Vitest (Vite Projects)

```bash
# npm
npm install --save-dev vitest

# Add to package.json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

**Note**: Vitest is recommended for Vite-based projects (faster, native ESM support).

---

## Writing Tests

### Basic Test Structure

```javascript
// sum.js
export function sum(a, b) {
  return a + b;
}

// sum.test.js
import { sum } from './sum';

describe('sum function', () => {
  test('adds 1 + 2 to equal 3', () => {
    expect(sum(1, 2)).toBe(3);
  });

  it('handles negative numbers', () => {
    expect(sum(-1, -1)).toBe(-2);
  });
});
```

### Test Organization

```javascript
describe('User Module', () => {
  describe('createUser', () => {
    it('creates user with valid data', () => {});
    it('throws error with invalid email', () => {});
  });

  describe('deleteUser', () => {
    it('deletes existing user', () => {});
    it('returns false for non-existent user', () => {});
  });
});
```

### Setup and Teardown

```javascript
describe('Database tests', () => {
  let db;

  beforeAll(async () => {
    // Run once before all tests
    db = await connectToDatabase();
  });

  afterAll(async () => {
    // Run once after all tests
    await db.close();
  });

  beforeEach(() => {
    // Run before each test
    db.clear();
  });

  afterEach(() => {
    // Run after each test
  });

  test('inserts data', () => {
    db.insert({ id: 1 });
    expect(db.count()).toBe(1);
  });
});
```

---

## Matchers

### Common Matchers

```javascript
// Exact equality
expect(2 + 2).toBe(4);
expect({ name: 'test' }).toEqual({ name: 'test' });

// Truthiness
expect(null).toBeNull();
expect(undefined).toBeUndefined();
expect(value).toBeDefined();
expect(true).toBeTruthy();
expect(false).toBeFalsy();

// Numbers
expect(value).toBeGreaterThan(3);
expect(value).toBeGreaterThanOrEqual(3);
expect(value).toBeLessThan(5);
expect(value).toBeLessThanOrEqual(5);
expect(0.1 + 0.2).toBeCloseTo(0.3);

// Strings
expect('hello world').toMatch(/world/);
expect('hello').toContain('ell');

// Arrays
expect(['a', 'b', 'c']).toContain('b');
expect([1, 2, 3]).toHaveLength(3);

// Objects
expect(obj).toHaveProperty('name');
expect(obj).toHaveProperty('user.email', 'test@example.com');
expect(obj).toMatchObject({ name: 'test' });
```

### Negation

```javascript
expect(value).not.toBe(false);
expect(array).not.toContain('x');
expect(obj).not.toHaveProperty('missing');
```

### Exception Testing

```javascript
// Sync exceptions
expect(() => {
  throw new Error('Invalid');
}).toThrow();

expect(() => {
  throw new Error('Invalid input');
}).toThrow('Invalid');

expect(() => {
  throw new Error('Invalid input');
}).toThrow(/invalid/i);

// Async exceptions
await expect(asyncFunction()).rejects.toThrow('Error');
await expect(asyncFunction()).rejects.toMatchObject({
  message: 'Error message'
});
```

---

## Mocking

### Function Mocks

```javascript
// Create mock function
const mockFn = jest.fn();  // Jest
const mockFn = vi.fn();    // Vitest

// Configure return value
mockFn.mockReturnValue(42);
mockFn.mockReturnValueOnce(1).mockReturnValueOnce(2);

// Configure implementation
mockFn.mockImplementation((x) => x * 2);

// Assertions
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockFn).toHaveBeenLastCalledWith('last');
```

### Module Mocking

```javascript
// Jest
jest.mock('./api', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'test' })
}));

// Vitest
vi.mock('./api', () => ({
  fetchData: vi.fn().mockResolvedValue({ data: 'test' })
}));

// Partial mock
jest.mock('./utils', () => ({
  ...jest.requireActual('./utils'),
  specificFunction: jest.fn()
}));
```

### Spying

```javascript
const obj = {
  method: () => 'original'
};

// Spy on method
const spy = jest.spyOn(obj, 'method');  // Jest
const spy = vi.spyOn(obj, 'method');    // Vitest

// Override implementation
spy.mockImplementation(() => 'mocked');

// Restore original
spy.mockRestore();
```

### Timer Mocking

```javascript
// Jest
jest.useFakeTimers();
jest.advanceTimersByTime(1000);
jest.runAllTimers();
jest.useRealTimers();

// Vitest
vi.useFakeTimers();
vi.advanceTimersByTime(1000);
vi.runAllTimers();
vi.useRealTimers();

// Example
test('debounce function', () => {
  jest.useFakeTimers();

  const callback = jest.fn();
  const debounced = debounce(callback, 500);

  debounced();
  expect(callback).not.toHaveBeenCalled();

  jest.advanceTimersByTime(500);
  expect(callback).toHaveBeenCalledTimes(1);
});
```

---

## Async Testing

### Promises

```javascript
// Return promise
test('async with promise', () => {
  return fetchData().then(data => {
    expect(data).toBe('result');
  });
});

// async/await
test('async with await', async () => {
  const data = await fetchData();
  expect(data).toBe('result');
});

// Resolves/Rejects
test('resolves correctly', async () => {
  await expect(fetchData()).resolves.toBe('result');
});

test('rejects with error', async () => {
  await expect(failingFetch()).rejects.toThrow('Error');
});
```

### Callbacks (Legacy)

```javascript
test('callback test', done => {
  fetchDataWithCallback((error, data) => {
    try {
      expect(error).toBeNull();
      expect(data).toBe('result');
      done();
    } catch (e) {
      done(e);
    }
  });
});
```

---

## Snapshots

### Basic Snapshots

```javascript
test('renders correctly', () => {
  const tree = renderer.create(<Button label="Click" />).toJSON();
  expect(tree).toMatchSnapshot();
});

// Inline snapshots
test('inline snapshot', () => {
  expect({ name: 'test', id: 1 }).toMatchInlineSnapshot(`
    {
      "id": 1,
      "name": "test",
    }
  `);
});
```

### Updating Snapshots

```bash
# Update all snapshots
jest --updateSnapshot
vitest --update

# Interactive mode
jest --watch
# Press 'u' to update failing snapshots
```

### Property Matchers

```javascript
test('snapshot with dynamic values', () => {
  const user = {
    id: Math.random(),
    name: 'test',
    createdAt: new Date()
  };

  expect(user).toMatchSnapshot({
    id: expect.any(Number),
    createdAt: expect.any(Date)
  });
});
```

---

## Configuration

### Jest (jest.config.js)

```javascript
/** @type {import('jest').Config} */
module.exports = {
  // Test environment
  testEnvironment: 'node',  // or 'jsdom' for browser

  // File patterns
  testMatch: ['**/__tests__/**/*.js', '**/*.test.js'],
  testPathIgnorePatterns: ['/node_modules/'],

  // Coverage
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Transformations
  transform: {
    '^.+\\.tsx?$': 'ts-jest'
  },

  // Module resolution
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy'
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js']
};
```

### Vitest (vite.config.ts)

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Test environment
    environment: 'jsdom',

    // Global APIs
    globals: true,

    // Setup files
    setupFiles: ['./tests/setup.ts'],

    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/']
    },

    // Include patterns
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}']
  }
});
```

---

## Testing Library Integration

### React Testing Library

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom
```

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from './Button';

test('button click handler', async () => {
  const handleClick = jest.fn();
  render(<Button onClick={handleClick}>Click Me</Button>);

  // Query elements
  const button = screen.getByRole('button', { name: /click me/i });

  // Interact
  fireEvent.click(button);

  // Assert
  expect(handleClick).toHaveBeenCalledTimes(1);
});

test('async content loading', async () => {
  render(<UserProfile userId={1} />);

  // Wait for async content
  await waitFor(() => {
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});
```

### Common Queries

```javascript
// Priority order (accessibility-first)
screen.getByRole('button', { name: 'Submit' });  // Best
screen.getByLabelText('Email');                   // Form fields
screen.getByPlaceholderText('Enter email');       // Fallback
screen.getByText('Welcome');                      // Static text
screen.getByTestId('custom-element');             // Last resort

// Query variants
getBy...    // Throws if not found
queryBy...  // Returns null if not found
findBy...   // Async, returns promise

// Multiple elements
getAllBy...
queryAllBy...
findAllBy...
```

### User Events

```javascript
import userEvent from '@testing-library/user-event';

test('form submission', async () => {
  const user = userEvent.setup();
  render(<LoginForm />);

  await user.type(screen.getByLabelText('Email'), 'test@example.com');
  await user.type(screen.getByLabelText('Password'), 'password123');
  await user.click(screen.getByRole('button', { name: 'Login' }));

  expect(await screen.findByText('Welcome')).toBeInTheDocument();
});
```

---

## Best Practices

### 1. Test Behavior, Not Implementation

```javascript
// Bad - tests implementation details
test('sets state correctly', () => {
  const { result } = renderHook(() => useCounter());
  expect(result.current.state.count).toBe(0);
});

// Good - tests behavior
test('increments counter', () => {
  render(<Counter />);
  fireEvent.click(screen.getByRole('button', { name: 'Increment' }));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```

### 2. Use Descriptive Test Names

```javascript
// Bad
test('test1', () => {});
test('works', () => {});

// Good
test('displays error message when email is invalid', () => {});
test('redirects to dashboard after successful login', () => {});
```

### 3. Arrange-Act-Assert Pattern

```javascript
test('adds item to cart', () => {
  // Arrange
  render(<ShoppingCart />);
  const addButton = screen.getByRole('button', { name: 'Add to Cart' });

  // Act
  fireEvent.click(addButton);

  // Assert
  expect(screen.getByText('1 item in cart')).toBeInTheDocument();
});
```

### 4. Avoid Test Interdependence

```javascript
// Bad - tests share state
let user;
beforeAll(() => { user = createUser(); });
test('test1', () => { modifyUser(user); });
test('test2', () => { /* depends on test1 */ });

// Good - each test is isolated
test('test1', () => {
  const user = createUser();
  modifyUser(user);
  expect(user.modified).toBe(true);
});
```

### 5. Mock External Dependencies

```javascript
// Mock API calls
jest.mock('./api');
api.fetchUser.mockResolvedValue({ name: 'Test User' });

// Mock timers for time-dependent code
jest.useFakeTimers();

// Mock browser APIs
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});
```

### 6. Test Edge Cases

```javascript
describe('validateEmail', () => {
  test.each([
    ['test@example.com', true],
    ['invalid-email', false],
    ['', false],
    [null, false],
    ['a@b.c', true],
    ['test+alias@example.com', true],
  ])('validates %s as %s', (email, expected) => {
    expect(validateEmail(email)).toBe(expected);
  });
});
```

---

## Quick Reference

### Jest Commands

```bash
jest                    # Run all tests
jest --watch            # Watch mode
jest --coverage         # With coverage
jest --updateSnapshot   # Update snapshots
jest path/to/test.js    # Run specific file
jest -t "test name"     # Run matching tests
```

### Vitest Commands

```bash
vitest                  # Watch mode (default)
vitest run              # Run once
vitest --coverage       # With coverage
vitest --update         # Update snapshots
vitest path/to/test.ts  # Run specific file
```

---

**Online References**:
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Vitest Documentation](https://vitest.dev/guide/)
- [Testing Library](https://testing-library.com/docs/)
