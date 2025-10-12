# 测试套件说明

为了让项目更贴近测试驱动开发（TDD）的实践，我们对测试目录进行了分层，并提供统一的覆盖率统计方式。测试按职责拆分为**单元测试**与**集成测试**两大类：

- `tests/unit/`：纯函数、工具方法等的快速测试，执行迅速且无外部依赖。
- `tests/integration/`：通过 FastAPI 应用和临时数据库运行的端到端测试，覆盖真实业务流程。

## 运行方式

### 1. 仅运行单元测试
```bash
uv run pytest tests/unit
```

### 2. 仅运行集成测试
```bash
uv run pytest tests/integration
```

> 集成测试会自动启动基于 SQLite 的临时数据库，并复用现有的异步客户端、Token 等高阶夹具。

### 3. 运行所有测试并生成覆盖率
```bash
uv run pytest
```

`pyproject.toml` 中的 `addopts` 默认启用了 `--cov`、`--cov-report=term-missing` 与 `--cov-branch`，执行任意测试命令都会自动输出覆盖率详情，并标注缺失的分支或语句。

## 目录结构概览

```
tests/
├── README.md               # 本说明文档
├── __init__.py
├── conftest.py             # 全局夹具与环境配置
├── integration/
│   ├── conftest.py         # 仅集成测试需要的数据库初始化
│   └── test_*.py           # API、权限、数据库等集成测试
└── unit/
    └── test_*.py           # 工具函数与纯逻辑单元测试
```

## 新增单元测试覆盖的核心能力

- `utils.password`: 哈希、验证与随机密码生成。  
- `utils.jwt`: 令牌创建、刷新、验证及异常场景。  
- `utils.response_adapter`: 新旧响应模型之间的适配逻辑。  
- `utils.cache`: 缓存键生成与装饰器逻辑（通过 FakeCacheManager 纯内存模拟）。

这些测试均使用 `pytest.mark.unit` 标记，可单独运行并在毫秒级完成，为 TDD 循环提供快速反馈。

## 常见命令速查

| 目标 | 命令 |
| --- | --- |
| 仅运行单元测试 | `uv run pytest -m unit` |
| 仅运行集成测试 | `uv run pytest -m integration` |
| 生成 HTML 覆盖率报告 | `uv run pytest --cov-report=html` |
| 查看最后一次测试的覆盖率明细 | `xdg-open htmlcov/index.html` |

> 由于在 `pyproject.toml` 中启用了 `--strict-markers`，若使用新的自定义标记，请记得将其添加到配置中。

## CI/CD 集成

GitHub Actions 会复用上述配置自动执行：

1. Ruff、mypy 等静态检查。
2. Pytest 全量测试（单元 + 集成）。
3. 覆盖率统计，并在终端输出缺失语句。

通过分层设计与高覆盖率的单元测试，项目具备了良好的 TDD 基础，可以在编码前先编写失败的测试，再迭代实现直至全部通过。🚀
