# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

This is an enterprise-grade FastAPI backend template with a clean three-layer architecture (API → Service → Repository → Model). It includes built-in RBAC permission management, user management, file management, and other core enterprise features. The project uses UV for package management and focuses on providing a clean, extensible backend framework.

## Common Commands

### Environment Setup
```bash
# Install UV package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Install development dependencies
uv sync --dev
```

### Development Server
```bash
# Run development server with hot reload
uv run uvicorn src:app --reload --host 0.0.0.0 --port 8000

# Run production server
uv run uvicorn src:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Operations
```bash
# Initialize database (first time setup)
uv run aerich init-db

# Generate migration after model changes
uv run aerich migrate --name "describe_your_changes"

# Apply migrations
uv run aerich upgrade

# View migration history
uv run aerich history
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_users.py

# Run with coverage report
uv run pytest --cov=src --cov-report=html
```

### Code Quality

#### 🔧 Pre-commit Hooks (自动化)
```bash
# hooks 会在 uv sync 时自动安装并配置
# 每次 git commit 时自动运行，确保代码质量

# 手动运行所有检查
uv run pre-commit run --all-files

# 禁用 hooks (如不需要)
uv run pre-commit uninstall

# 跳过单次检查 (紧急提交)
git commit --no-verify -m "urgent fix"
```

#### ⚙️ 手动检查命令
```bash
# 代码检查和自动修复 (替代 black + isort)
uv run ruff check --fix src/

# 代码格式化
uv run ruff format src/

# 类型检查 (可选)
uv run mypy src/
```

📖 **详细配置**: 查看 [docs/pre-commit-guide.md](docs/pre-commit-guide.md)

### Docker Operations
```bash
# Build image
docker build -t backend-template .

# Run container
docker run -p 8000:8000 backend-template
```

### Documentation
```bash
# Install documentation dependencies
uv sync --group docs

# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build

# Deploy documentation to GitHub Pages
uv run mkdocs gh-deploy
```

## Architecture Overview

The project follows a clean three-layer architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  (src/api/v1/) - Routes, parameter validation, responses    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  (src/services/) - Business logic, permissions, validation  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                          │
│  (src/repositories/) - Data access, CRUD operations         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                            │
│  (src/models/) - Tortoise ORM models, database schemas     │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles
- **Single Responsibility**: Each layer handles only its own logic
- **Dependency Injection**: Managed through FastAPI's dependency system
- **Type Safety**: Comprehensive Python type annotations throughout
- **Async First**: All I/O operations are asynchronous
- **Security First**: Multiple built-in security mechanisms

### Core Components

- **Authentication**: JWT-based with access tokens (4 hours) and refresh tokens (7 days)
- **Authorization**: RBAC system with roles, menus, and API permissions
- **Rate Limiting**: Login throttling (5 attempts/minute) and refresh token limiting (10/minute)
- **File Management**: Secure file upload/download with type validation and size limits
- **Audit Logging**: Comprehensive user activity tracking
- **Caching**: Redis integration with smart caching strategies

## Development Workflow for New Features

When adding new functionality, follow this standard process:

1. **Define Model** (`src/models/admin.py`) - Create Tortoise ORM model
2. **Create Schema** (`src/schemas/`) - Define Pydantic validation schemas
3. **Implement Repository** (`src/repositories/`) - Add data access layer
4. **Write Service** (`src/services/`) - Implement business logic
5. **Add API Routes** (`src/api/v1/`) - Create endpoint handlers
6. **Generate Migration** - Run `uv run aerich migrate --name "feature_name"`
7. **Write Tests** (`tests/`) - Add test coverage

## Security Considerations

- JWT tokens are configured with HS256 algorithm
- Default admin credentials: username=`admin`, password=`abcd1234` (change immediately!)
- Password requirements: minimum 8 characters with letters and numbers
- File upload restrictions: whitelist validation, size limits, dangerous file detection
- Production checklist:
  - Set `DEBUG=False`
  - Generate strong `SECRET_KEY` with `openssl rand -hex 32`
  - Configure proper `CORS_ORIGINS`
  - Use PostgreSQL instead of SQLite
  - Set strong `SWAGGER_UI_PASSWORD`

## Database Best Practices

- Models inherit from `BaseModel` and `TimestampMixin` for consistency
- Use `select_related()` for foreign key preloading
- Use `prefetch_related()` for many-to-many optimization
- Add indexes on frequently queried fields
- String references for relationships to avoid circular imports: `fields.ForeignKeyField("models.User")`

## Environment Configuration

Key environment variables (configured in `.env`):
- `SECRET_KEY`: JWT signing key (required, auto-generated if missing)
- `APP_ENV`: development/production
- `DB_ENGINE`: sqlite/postgres
- `CORS_ORIGINS`: Allowed origins for CORS
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiry (default: 240)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiry (default: 7)

## Important Notes

- All routes are async - use `await` for database operations
- Repository pattern is used for data access - avoid direct model queries in services
- Services handle business logic and permissions - keep routes thin
- Use dependency injection for authentication: `current_user: User = DependAuth`
- For admin-only endpoints use: `current_user: User = SuperUserRequired`
- When modifying models, always generate and apply migrations
- The project uses UV for dependency management - avoid pip directly

## API Documentation

After starting the server:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/base/health
- Version info: http://localhost:8000/api/v1/base/version
