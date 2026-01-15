<h1 align="center">
    iGrant.io Dataspace Backend
</h1>

<p align="center">
    <a href="/../../commits/" title="Last Commit"><img src="https://img.shields.io/github/last-commit/decentralised-dataexchange/data-space-backend?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img src="https://img.shields.io/github/issues/decentralised-dataexchange/data-space-backend?style=flat"></a>
    <a href="./LICENSE" title="License"><img src="https://img.shields.io/badge/License-Apache%202.0-yellowgreen?style=flat"></a>
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#development">Development</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#licensing">Licensing</a>
</p>

## About

This repository hosts the source code for the reference implementation of the iGrant.io Dataspace Backend. The backend provides REST APIs for managing agreements, credentials, organisations, services, and B2B connections within the iGrant.io ecosystem.

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| [Python](https://www.python.org/) | 3.8+ | Programming language |
| [Django](https://www.djangoproject.com/) | 3.0.x | Web framework |
| [Django REST Framework](https://www.django-rest-framework.org/) | 3.13.x | REST API toolkit |
| [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/) | 4.3.x | JWT authentication |
| [Poetry](https://python-poetry.org/) | 1.x | Dependency management |
| [Gunicorn](https://gunicorn.org/) | 20.x | WSGI HTTP server |
| [PostgreSQL](https://www.postgresql.org/) | - | Production database |
| [SQLite](https://www.sqlite.org/) | - | Development database |
| [Ruff](https://docs.astral.sh/ruff/) | 0.11.x | Linter and formatter |

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker (recommended for development)
- Poetry (for local development without Docker)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/decentralised-dataexchange/data-space-backend.git
   cd data-space-backend
   ```

2. Build the Docker image:
   ```bash
   make build
   ```

3. Run the development server:
   ```bash
   make run
   ```

4. Open [http://localhost:8000](http://localhost:8000) in your browser.

### Admin Dashboard

Django admin dashboard is accessible at [http://localhost:8000/admin/](http://localhost:8000/admin/) with default credentials:

| Field | Value |
|-------|-------|
| Email | admin@example.com |
| Password | admin |

## Development

### Available Commands

| Command | Description |
|---------|-------------|
| `make` | Show all available commands |
| `make build` | Build the Docker image |
| `make run` | Run backend locally for development |
| `make build/docker/deployable` | Build deployable Docker image for staging/production |
| `make publish` | Publish Docker image to registry |
| `make deploy/staging` | Deploy to staging K8s cluster |
| `make docs/run` | Run OpenAPI documentation |
| `make docs/bundle` | Bundle OpenAPI documentation |

### Project Structure

```
data-space-backend/
├── authorization/              # Authorization and permissions
├── b2b_connection/             # B2B connection management
├── config/                     # Application configuration
├── connection/                 # Connection handling
├── customadminsite/            # Custom Django admin site
├── data_disclosure_agreement/  # Data Disclosure Agreement templates
├── data_disclosure_agreement_record/  # DDA records
├── dataspace_backend/          # Main Django project settings
├── discovery/                  # Discovery services
├── notification/               # Notification system
├── oAuth2Clients/              # OAuth2 client management
├── onboard/                    # User onboarding and authentication
├── openapi/                    # OpenAPI documentation
├── organisation/               # Organisation management
├── resources/                  # Docker and deployment resources
├── service/                    # Service management
├── software_statement/         # Software statement handling
├── webhook/                    # Webhook integrations
├── Makefile                    # Build and development commands
├── manage.py                   # Django management script
└── pyproject.toml              # Python dependencies and tools config
```

## Configuration

### Environment Variables

For production deployment, configure the following environment variables:

| Variable | Description |
|----------|-------------|
| `ENV` | Set to `prod` for production mode |
| `POSTGRES_NAME` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_HOST` | PostgreSQL host address |
| `DATA_MARKETPLACE_DW_URL` | Data marketplace DW URL |
| `DATA_MARKETPLACE_APIKEY` | Data marketplace API key |

### Local Development (Without Docker)

1. Install Poetry:
   ```bash
   pip install poetry
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run migrations:
   ```bash
   poetry run python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   poetry run python manage.py createsuperuser
   ```

5. Start the development server:
   ```bash
   poetry run python manage.py runserver
   ```

## Deployment

### Docker Deployment

1. Build the deployable image:
   ```bash
   make build/docker/deployable
   ```

2. Publish to registry:
   ```bash
   make publish
   ```

3. Deploy to staging:
   ```bash
   make deploy/staging
   ```

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

If you find any problems, please [create an issue](https://github.com/decentralised-dataexchange/data-space-backend/issues) in this repository.

## Licensing

Copyright (c) 2023-25 LCubed AB (iGrant.io), Sweden

Licensed under the Apache 2.0 License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the [LICENSE](./LICENSE) for the specific language governing permissions and limitations under the License.
