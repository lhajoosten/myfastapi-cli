# myfastapi-cli

A custom CLI tool to scaffold Clean Architecture FastAPI backend projects with optional vertical-slice modularity and built-in authentication.

---

## Features

- **Scaffold new FastAPI backend projects** with a single command
- **Clean Architecture**: Domain, Application, Infrastructure, Presentation, Core
- **Optional modular mode** for vertical-slice, domain-driven project structure
- **Built-in authentication** (JWT, roles, extendable)
- **Add new modules** to existing projects (vertical slice)
- **Direct folder copy** (no cookiecutter needed)
- **Extensible**: Easily add features, entities, CQRS handlers, and services

---

## Quickstart

### 1. Install the CLI locally

```bash
git clone https://github.com/lhajoosten/myfastapi-cli.git
cd myfastapi-cli
pip install -e .
```

### 2. Generate a new project

```bash
myfastapi new myproject
```

- By default, this uses a layered structure for a single-domain project.

#### Modular (vertical slice) mode

```bash
myfastapi new myproject --modular
# You'll be prompted for module names, e.g. "auth,finance,weather"
```

### 3. Add new modules (modular projects only)

```bash
myfastapi add-module analytics
```

### 4. Run your generated project

```bash
cd myproject
uvicorn app.main:app --reload
```

---

## Project Structure

### Default (Layered)

```
myproject/
├── app/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   └── value_objects/
│   │   │   ├── __init__.py
│   │   │   └── email.py
│   │   │   └── address.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── interfaces/
│   │   │   │   ├── __init__.py
│   │   │   │   └── command_repository.py
│   │   │   │   └── query_repository.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── result_model.py
│   │   ├── authentication/
│   │   │   ├── __init__.py
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   └── register_user.py
│   │   │   │   └── login_user.py
│   │   │   │   └── reset_password.py
│   │   │   ├── queries/
│   │   │   │   ├── __init__.py
│   │   │   │   └── get_user.py
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       └── auth_service.py
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   └── create_user.py
│   │   │   │   └── update_user.py
│   │   │   │   └── delete_user.py
│   │   │   ├── queries/
│   │   │   │   ├── __init__.py
│   │   │   │   └── get_user_by_id.py
│   │   │   │   └── list_users.py
│   │   │   └── services/
│   │   │       ├── __init__.py
│   │   │       └── user_service.py
│   │   │   ├── dtos/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_dto.py
│   │   │   └── mappers/
│   │   │       ├── __init__.py
│   │   │       └── user_mapper.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── command_repository.py
│   │   │   └── query_repository.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py
│   │   └── jwt/
│   │       ├── __init__.py
│   ├── presentation/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routers/
│   │   │       ├── __init__.py
│   │   │       └── auth_controller.py
│   │   └── middleware/
│   │       ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── logging.py
│       ├── config.py
│       └── di.py
├── tests/
│   └── unit/
│   │   └── application/
│   │   │   └── authentication/
│   │   │   │   ├── __init__.py
│   │   │   │   └── test_register_user.py
│   │   │   │   └── test_login_user.py
│   │   │   └── users/
│   │   │   │   ├── __init__.py
│   │   │   │   └── test_create_user.py
│   │   │   │   └── test_get_user_by_id.py
│   └── integration/
│   │   └── infrastructure/
│   │   │   ├── __init__.py
│   │   │   └── test_command_repository.py
│   │   │   └── test_query_repository.py
│   │   └── presentation/
│   │   │   ├── __init__.py
│   │   │   └── test_auth_controller.py
│   │   │   └── test_user_controller.py
│   └── conftest.py
├── migrations/
├── requirements.txt
├── Dockerfile
└── README.md

```

### Modular (Vertical Slice)

```
myproject/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   └── value_objects/
│   │   │       ├── __init__.py
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── common/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── interfaces/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── models/
│   │   │   │   │   ├── __init__.py
│   │   │   ├── authentication/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── commands/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── __init__.py
│   │   │   │   └── services/
│   │   │   │       ├── __init__.py
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── commands/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── queries/
│   │   │   │   │   ├── __init__.py
│   │   │   │   └── services/
│   │   │   │       ├── __init__.py
│   │   │   ├── dtos/
│   │   │   │   ├── __init__.py
│   │   │   └── mappers/
│   │   │       ├── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   ├── db/
│   │   │   │   ├── __init__.py
│   │   │   └── jwt/
│   │   │       ├── __init__.py
│   │   ├── presentation/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routers/
│   │   │   │       ├── __init__.py
│   │   │   └── middleware/
│   │   │       ├── __init__.py
│   ├── <...other modules...>
│   ├── module x/
│   │   ├── __init__.py
│   │   ├── <...other sub folders..>
│   ├── module y/
│   │   ├── __init__.py
│   │   ├── <...other sub folders..>
│   ├── module z/
│   │   ├── __init__.py
│   │   ├── <...other sub folders..>
│   └── core/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── logging.py
│       ├── config.py
│       └── di.py
├── tests/
│   ├── __init__.py
│   └── unit/
│   │   ├── __init__.py
│   │   └── application/
│   │       ├── __init__.py
│   │       └── authentication/
│   │           ├── __init__.py
│   │       └── users/
│   │           ├── __init__.py
│   └── integration/
│   │   ├── __init__.py
│   │   └── infrastructure/
│   │       ├── __init__.py
│   │   └── presentation/
│   │       ├── __init__.py
│   └── conftest.py
├── migrations/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Built-in Authentication

- Ready-to-use JWT authentication endpoints, user entity, role-based access decorators, and extendable for OAuth.
- Secure by default, and easily customizable.

---

## Using with GitHub Copilot & PyCharm

- This project is structured for maximum Copilot compatibility.
- See the `.copilot-instructions` file for prompt engineering and codegen best practices.
- Use the suggested file structure and comments to encourage Copilot to generate idiomatic code.

---

## Contributing

1. Fork & clone the repo
2. Create a new branch (`feature/your-feature`)
3. Add tests and documentation for any new features
4. Submit a pull request

---

## Roadmap

- [x] Scaffold new project (layered and modular)
- [x] Built-in authentication
- [ ] Add CQRS/CRUD code generators
- [ ] Support for more auth providers (OAuth, SSO)
- [ ] Built-in AI service abstraction
- [ ] Optional Celery integration
- [ ] Frontend scaffold generator

---

## License

MIT

---
