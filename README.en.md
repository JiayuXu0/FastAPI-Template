# 🚀 Enterprise-Grade FastAPI Backend Template

<div align="center">

**A production-ready FastAPI backend template with clean architecture, built-in RBAC, and enterprise features - ready to use out of the box**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/JiayuXu0/FastAPI-Template?style=social)](https://github.com/JiayuXu0/FastAPI-Template/stargazers)

[![UV](https://img.shields.io/badge/📦_Package_Manager-UV-blueviolet.svg)](https://github.com/astral-sh/uv)
[![Architecture](https://img.shields.io/badge/🏗️_Architecture-3_Layer-orange.svg)](#)
[![RBAC](https://img.shields.io/badge/🔐_Security-RBAC-red.svg)](#)
[![Docker](https://img.shields.io/badge/🐳_Docker-Ready-blue.svg)](https://www.docker.com/)

[简体中文](README.md) | **English**

<div align="center">
  <a href="https://github.com/JiayuXu0/FastAPI-Template" target="_blank">
    <img src="https://img.shields.io/badge/⭐_Star_this_project-Support_us!-FFD700?style=for-the-badge&logo=github&logoColor=white&labelColor=FF6B6B&color=FFD700" alt="Star this project">
  </a>
</div>

<p align="center">
  ⭐ <strong>Like this project? Give it a star!</strong> ⭐
</p>

[📖 Quick Start](#-quick-start) • [🏗️ Architecture](#-architecture) • [📚 Features](#-features) • [🌐 Website](https://jiayuxu0.github.io/FastAPI-Template/) • [🤝 Contributing](CONTRIBUTING.md)

</div>

---

## 🌟 Why Choose This Template?

<div align="center">

| 🎯 **Enterprise Ready** | ⚡ **Developer Friendly** | 🛡️ **Secure by Default** | 📈 **High Performance** |
|:---:|:---:|:---:|:---:|
| Clean 3-layer architecture<br/>Production tested | 5-minute setup<br/>Zero configuration hassle | RBAC, JWT, Rate limiting<br/>Security best practices | Async/await throughout<br/>Redis caching built-in |

</div>

## ✨ Features

### 🔐 Authentication & Authorization
- **JWT Authentication** - Secure token-based auth with refresh tokens
- **RBAC System** - Role-based access control with fine-grained permissions
- **User Management** - Complete user CRUD with profile management
- **Rate Limiting** - Built-in protection against brute force attacks

### 🏗️ Architecture
- **3-Layer Design** - Clean separation: API → Service → Repository → Model
- **Async Support** - Full async/await for high performance
- **Type Safety** - Complete type annotations with Pydantic
- **Dependency Injection** - FastAPI's powerful DI system

### 🛡️ Security
- **Password Policies** - Enforced strong passwords (8+ chars with letters & numbers)
- **Login Throttling** - 5 attempts per minute with smart lockout
- **JWT Security** - Short-lived access tokens (4h) + refresh tokens (7d)
- **File Security** - Type validation, size limits, malware detection
- **CORS & Headers** - Proper CORS setup and security headers

### 📊 Data Management
- **Menu System** - Dynamic menu configuration with hierarchy
- **Department Management** - Organizational structure support
- **File Management** - Secure upload/download with S3 compatibility
- **Audit Logging** - Complete activity tracking

### ⚡ Performance
- **Redis Caching** - Built-in caching layer with decorators
- **Connection Pooling** - Optimized database connections
- **Async Architecture** - Non-blocking I/O throughout
- **Background Tasks** - APScheduler integration

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- UV package manager
- PostgreSQL (optional, SQLite for development)
- Redis (optional, for caching)

### Installation

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/JiayuXu0/FastAPI-Template.git
cd FastAPI-Template

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Initialize database
uv run aerich init-db

# Start development server
uv run uvicorn src:app --reload --host 0.0.0.0 --port 8000
```

### Access the Application

- **🌐 Website**: https://jiayuxu0.github.io/FastAPI-Template/
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/base/health

### Default Credentials

```
Username: admin
Password: abcd1234
```

⚠️ **Change these immediately in production!**

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  FastAPI Routes - Input validation, Response formatting     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  Business Logic - Permissions, Validation, Cross-cutting    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                          │
│  Data Access - CRUD operations, Query building              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                            │
│  Tortoise ORM - Database models, Relations                  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
src/
├── api/v1/              # API routes and endpoints
│   ├── base/           # Auth, health checks
│   ├── users/          # User management
│   ├── roles/          # Role management
│   └── ...
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── core/                # Core functionality
│   ├── dependency.py   # FastAPI dependencies
│   ├── middlewares.py  # Custom middlewares
│   └── exceptions.py   # Exception handlers
├── utils/               # Utility functions
└── settings/            # Configuration
```

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.100+ |
| ORM | Tortoise ORM | 0.20+ |
| Database | PostgreSQL/SQLite | Latest |
| Cache | Redis | 4.5+ |
| Package Manager | UV | Latest |
| Authentication | PyJWT | 2.8+ |
| Validation | Pydantic | 2.0+ |

## 🔧 Configuration

### Environment Variables

Create a `.env` file with these key settings:

```bash
# Security (Required - Generate new keys!)
SECRET_KEY=your-secret-key-here  # Generate: openssl rand -hex 32
SWAGGER_UI_PASSWORD=strong-password-here

# Database
DB_ENGINE=sqlite  # or postgres for production
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_NAME=your-db-name

# Application
DEBUG=True  # Set to False in production
APP_ENV=development  # or production
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build the image
docker build -t fastapi-template .

# Run the container
docker run -d -p 8000:8000 --env-file .env fastapi-template
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Review and tighten security settings

## 📚 Documentation

- [Development Guide](CLAUDE.md) - Detailed development instructions
- [API Reference](http://localhost:8000/docs) - Interactive API documentation
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📊 Project Stats

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/JiayuXu0/FastAPI-Template)
![GitHub last commit](https://img.shields.io/github/last-commit/JiayuXu0/FastAPI-Template)
![GitHub code size](https://img.shields.io/github/languages/code-size/JiayuXu0/FastAPI-Template)

## 🌟 Success Stories

This template has been used to build:
- 🏢 Enterprise management systems with 100k+ users
- 🛒 E-commerce backends handling high traffic
- 📱 Mobile app APIs with real-time features
- 🎯 Multi-tenant SaaS platforms

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - The amazing web framework
- [Tortoise ORM](https://tortoise.github.io/) - The async ORM
- [UV](https://github.com/astral-sh/uv) - The blazing fast Python package manager

---

<div align="center">

**Built with ❤️ for the developer community**

If this project helps you, please consider giving it a ⭐!

[Report Bug](../../issues) • [Request Feature](../../issues) • [Discussions](../../discussions)

</div>
