# GEMINI.md

## Project Overview

This is a multi-step checklist management system built with Python and the Django framework. The application helps users organize and execute complex workflows by defining reusable checklist templates.

The key components of the technical stack are:
*   **Backend:** Django
*   **Frontend:** Django Templates with HTMX for dynamic interactions, styled with Tailwind CSS and DaisyUI.
*   **Database:** PostgreSQL for production/docker and SQLite for local development.
*   **Package Management:** `uv` is used for managing Python dependencies.
*   **Containerization:** The project is fully containerized with Docker and includes a `docker-compose.yaml` for orchestration.

## Building and Running

### Local Development (using `uv`)

The `README.md` provides instructions for setting up the local development environment.

1.  **Environment Variables:** Create a `.env` file in the `checklistapp/` directory by copying the `checklistapp/.env.dist` template and filling in the required values.
2.  **Install Dependencies:**
    ```bash
    uv sync
    ```
3.  **Database Migration:**
    ```bash
    uv run python manage.py migrate
    ```
4.  **Create Superuser:**
    ```bash
    uv run python manage.py createsuperuser
    ```
5.  **Run Development Server:**
    ```bash
    uv run python manage.py tailwind start
    uv run python manage.py runserver
    ```

### Docker

The project can be run using Docker Compose.

```bash
docker-compose up
```

This will build the images and start the `app`, `db`, and `nginx` services. The application will be accessible at `http://localhost:80`.

## Testing

Tests are written using `pytest` and can be run with the following command from the `checklistapp/` directory:

```bash
uv run pytest
```

The CI pipeline, defined in `.github/workflows/tests.yml`, also runs these tests against a PostgreSQL database. Coverage reports are generated as part of the test run.

## Development Conventions

*   **Code Style:** The project uses `ruff` for code formatting and linting. The configuration is in `pyproject.toml`. Before committing, you can run the following commands to format and lint the code:
    ```bash
    uv run ruff format .
    uv run ruff check --fix .
    ```
    The `prepare_build.bat` script is also available to automate this.

*   **Dependencies:** Project dependencies are managed in `pyproject.toml`. The `requirements.txt` file is generated from `pyproject.toml` using the `uv export` command.

*   **Branching:** The CI workflow in `.github/workflows/tests.yml` is triggered on pull requests to the `master` branch.
