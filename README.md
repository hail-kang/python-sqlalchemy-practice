# Python SQLAlchemy Practice

A comprehensive collection of SQLAlchemy patterns, best practices, and solutions to common problems encountered in real-world applications.

## Project Purpose

This project demonstrates practical solutions to real-world SQLAlchemy ORM challenges through working code examples and best practices. Each topic is organized with clear problem/solution pairs showing the WHY behind each pattern.

## Topics Covered

### 01. Mapped Column Basics
- **Modern SQLAlchemy 2.0 patterns** vs legacy patterns
- **Type safety** with `Mapped[T]` and `mapped_column()`
- **Why migrate** from old-style Column definitions

### 02. Default Values
- **Python-level defaults** vs database-level defaults
- **When to use each** strategy
- **Timezone handling** with UTC

### 03. Session Pool
- **Connection pooling** strategies (NullPool, QueuePool, StaticPool)
- **Pool exhaustion** prevention and detection
- **Production vs development** configurations

### 04. N+1 Problem
- **Problem demonstration** with lazy loading
- **Solutions**: selectinload(), joinedload(), subqueryload()
- **Performance comparison** with metrics
- **Handling cases without foreign keys**

### 05. Bulk Operations
- **Bulk insert strategies** comparison
- **Bulk update patterns** for different scenarios
- **Performance trade-offs** and when to use each

### 06. Partial Select
- **Column-level optimization** with load_only()
- **Type safety** with TypedDict, Dataclass, Pydantic
- **Memory and performance** benefits

### 07. Concurrency Control
- **Race conditions** and their dangers
- **Pessimistic locking** with SELECT FOR UPDATE
- **Real-world example**: Campaign participant limits
- **SQLite limitations** and production recommendations

## Tech Stack

- **Python**: 3.10+
- **SQLAlchemy**: 2.0+
- **Database**: SQLite (examples), PostgreSQL/MySQL (production recommended)
- **Package Manager**: uv
- **Code Quality**: ruff, pyright

## Getting Started

### Prerequisites

- Python 3.10 or higher
- uv package manager

### Installation

```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd python-sqlalchemy-practice

# Install dependencies
uv sync
```

### Activate Virtual Environment

```bash
# Activate .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

## Project Structure

```
python-sqlalchemy-practice/
├── src/
│   ├── examples/
│   │   ├── 01_mapped_column_basics/   # Modern SQLAlchemy 2.0 patterns
│   │   ├── 02_default_values/         # Python vs database defaults
│   │   ├── 03_session_pool/           # Connection pooling strategies
│   │   ├── 04_n_plus_one_problem/     # N+1 problem and solutions
│   │   ├── 05_bulk_operations/        # Bulk insert/update patterns
│   │   ├── 06_partial_select/         # Column-level optimization
│   │   └── 07_concurrency/            # Race conditions and locking
│   ├── models/                        # SQLAlchemy models
│   │   ├── base.py                    # Base model with common fields
│   │   ├── user.py                    # User model
│   │   ├── post.py                    # Post model
│   │   ├── comment.py                 # Comment model
│   │   ├── campaign.py                # Campaign model
│   │   └── application.py             # Application model
│   ├── config/
│   │   └── database.py                # Database configuration
│   └── utils/
│       ├── db_init.py                 # Database initialization
│       └── sample_data.py             # Sample data generation
├── pyproject.toml                     # Project configuration
├── .python-version                    # Python version (3.10)
└── README.md
```

## Development Guide

### Code Quality Management

```bash
# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Type checking
uv run pyright
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_bulk_operations.py

# Check coverage
uv run pytest --cov=src
```

### Enable SQL Query Logging

```python
import logging

# Configure SQLAlchemy engine logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or enable detailed logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```

## Running Examples

Each example can be run independently. Navigate to each example folder and check the README for detailed explanations.

```bash
# 01. Modern SQLAlchemy patterns
uv run python -m src.examples.01_mapped_column_basics.good_mapped_column

# 02. Default values comparison
uv run python -m src.examples.02_default_values.good_python_defaults

# 03. Session pool (see multiple examples)
uv run python -m src.examples.03_session_pool.bad_nullpool_no_pool
uv run python -m src.examples.03_session_pool.good_queuepool_with_pool

# 04. N+1 problem demonstration
uv run python -m src.examples.04_n_plus_one_problem.bad_lazy_loading
uv run python -m src.examples.04_n_plus_one_problem.good_eager_loading

# 05. Bulk operations
uv run python -m src.examples.05_bulk_operations.bad_individual_inserts
uv run python -m src.examples.05_bulk_operations.good_bulk_insert

# 06. Partial select with type safety
uv run python -m src.examples.06_partial_select.good_partial_select

# 07. Concurrency and race conditions
uv run python -m src.examples.07_concurrency.bad_campaign_overflow
uv run python -m src.examples.07_concurrency.good_campaign_safe
```

## Key Learning Points

### Base Model Pattern
- Simple `Base` class with common fields (id, created_at, updated_at)
- Auto-generated table names from class names
- Python-level defaults for database independence

### Models
- **User**: Basic user with username, email, full_name
- **Post**: Blog posts with author relationship
- **Comment**: Comments on posts
- **Campaign**: Marketing campaigns with participant limits
- **Application**: User applications to campaigns with status tracking

### Real-World Patterns
1. **N+1 Problem**: Always use eager loading (selectinload/joinedload) for relationships
2. **Bulk Operations**: Use `bulk_insert_mappings()` for large datasets (10x faster)
3. **Type Safety**: Use TypedDict/Dataclass/Pydantic for partial selects
4. **Concurrency**: Always use SELECT FOR UPDATE for critical sections
5. **Connection Pooling**: Use QueuePool in production, NullPool in tests

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Performance Tips](https://docs.sqlalchemy.org/en/20/faq/performance.html)

## Contributing

Issues and Pull Requests are always welcome!

## License

MIT License
