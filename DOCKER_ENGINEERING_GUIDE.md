# Docker Engineering Guide

This guide is a practical reference for using Docker in real projects without falling into tutorial hell. It focuses on what matters when containerizing applications, reviewing generated Docker files, and shipping reliably.

## Core Mental Model

Docker packages an application and its runtime environment so it can run consistently across machines.

Key terms:

- **Image**: A built package containing your app, dependencies, runtime, and startup command.
- **Container**: A running instance of an image.
- **Dockerfile**: The recipe used to build an image.
- **Build context**: The directory Docker can access during `docker build`.
- **`.dockerignore`**: Controls what is excluded from the build context.
- **Compose**: A tool for running multiple containers together, usually app + database + cache.
- **Volume**: Persistent storage managed outside the container lifecycle.
- **Bind mount**: A local folder mounted into a container, useful during development.
- **Port mapping**: Connects a port on your machine to a port inside the container.
- **Environment variables**: Runtime configuration injected into the container.
- **Registry**: A place where images are stored, such as Docker Hub, GitHub Container Registry, AWS ECR, or Render's registry.

The important distinction:

```text
Dockerfile builds the app.
Compose runs the app.
The image should be portable.
The container should be disposable.
Data and secrets should live outside the image.
```

## Recommended Workflow

Use this as your default engineering workflow:

```text
1. Start with docker init or a known-good template.
2. Review the generated Dockerfile, Compose file, and .dockerignore.
3. Replace generic defaults with project-specific choices.
4. Verify secrets are not copied into the image.
5. Build the image.
6. Run the container locally.
7. Check logs and app behavior.
8. Run tests inside the container when possible.
9. Push the image to a registry if needed.
10. Deploy with environment variables supplied by the platform.
```

`docker init` is acceptable as a starting point. It is not something to trust blindly. Treat it like scaffolding.

AI tools are useful for review, explanation, and debugging. They should assist your judgment, not replace it.

## What To Use In Practice

For small learning projects:

```text
docker init
docker compose up --build
review generated files
fix obvious issues
```

For real projects:

```text
custom Dockerfile
custom .dockerignore
Compose for local development
managed services or platform config for production
CI build verification
```

For this Flask project, the app should be served with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 run:app
```

Avoid using Flask's development server in a production image.

## Dockerfile Methodology

A good Dockerfile should be boring, explicit, and easy to audit.

General structure:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends required-system-packages \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

Important principles:

- Pin the runtime family, for example `python:3.11-slim`.
- Copy dependency files before app code to improve build caching.
- Do not copy `.env` into the image.
- Do not install unnecessary OS packages.
- Use `--no-cache-dir` for Python package installation.
- Use a real production server for web apps.
- Keep the startup command clear.
- Avoid clever shell scripts unless the project really needs them.

## `.dockerignore` Methodology

The `.dockerignore` file prevents unnecessary or sensitive files from entering the Docker build context.

Typical Python `.dockerignore`:

```dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd

venv/
.venv/
env/

.git/
.gitignore

.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

.env
*.db
instance/

.DS_Store
.vscode/
.idea/
```

Security rule:

```text
If a file contains secrets, credentials, tokens, private keys, local databases, or personal config, it should not be copied into the image.
```

## Compose Methodology

Compose is mainly for local development and local integration testing.

Use Compose when:

- Your app needs a database.
- Your app needs Redis, Mongo, queues, workers, or other services.
- You want a one-command local setup.
- You want consistent developer onboarding.

Typical local Compose shape:

```yaml
services:
  web:
    build:
      context: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    command: gunicorn --bind 0.0.0.0:5000 --reload run:app
```

For production-like Compose, remove live reload and bind mounts:

```yaml
services:
  web:
    build:
      context: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    command: gunicorn --bind 0.0.0.0:5000 run:app
```

Development Compose and production deployment are not always the same thing. In industry, production is often handled by a platform such as Render, Fly.io, ECS, Kubernetes, Railway, or Cloud Run.

## Environment Variables And Secrets

Environment variables should be supplied at runtime.

Good:

```yaml
env_file:
  - .env
```

Good in deployment platforms:

```text
Set SECRET_KEY, DATABASE_URL, API keys, and OAuth secrets in the platform dashboard.
```

Bad:

```dockerfile
ENV GEMINI_API_KEY=real-secret-value
```

Bad:

```dockerfile
COPY .env .
```

Rules:

- Never bake secrets into Docker images.
- Never commit `.env` files.
- Use `.env.example` for documentation.
- Rotate secrets if they were accidentally copied, committed, or pushed.
- Treat image registries as places where many people or systems may eventually have access.

## Databases And Persistent Data

Containers are disposable. Databases are not.

For local development:

- SQLite can be fine for quick testing.
- Postgres in Compose is better when the production app uses Postgres.
- Use named volumes for database persistence.

Example:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

For production:

- Prefer managed databases unless you are explicitly responsible for database operations.
- Use Supabase, RDS, Neon, Render Postgres, Cloud SQL, or similar.
- Do not store production database files only inside an app container.

## Ports

Inside the container, your app listens on a container port:

```text
0.0.0.0:5000
```

Your machine maps to it:

```yaml
ports:
  - "5000:5000"
```

The left side is your host machine.

The right side is inside the container.

```text
host:container
```

If your app is unreachable, check:

- Is the app binding to `0.0.0.0`, not `127.0.0.1`?
- Is the correct container port exposed?
- Is the Compose port mapping correct?
- Is another process already using the host port?

## Build And Run Commands

Build an image:

```bash
docker build -t my-app .
```

Run it:

```bash
docker run --rm -p 5000:5000 --env-file .env my-app
```

Run with Compose:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
```

Show logs:

```bash
docker compose logs -f
```

Open a shell:

```bash
docker compose exec web sh
```

Stop containers:

```bash
docker compose down
```

Stop and remove volumes:

```bash
docker compose down -v
```

Use `down -v` carefully because it deletes persistent local data.

## Testing With Docker

Run tests inside the container when the goal is to verify the containerized environment:

```bash
docker compose run --rm web pytest
```

This catches issues that local virtual environments may hide.

Examples:

- Missing system packages.
- Wrong Python version.
- Incorrect working directory.
- Missing environment variables.
- Files excluded by `.dockerignore`.
- App starts locally but fails inside the container.

## Image Publishing

Build and tag:

```bash
docker build -t username/app-name:latest .
```

Login:

```bash
docker login
```

Push:

```bash
docker push username/app-name:latest
```

Better tagging practice:

```text
username/app-name:latest
username/app-name:1.0.0
username/app-name:git-sha
```

Avoid relying only on `latest` for production releases. It is convenient but ambiguous.

## Security Checklist

Before shipping, verify:

- `.env` is in `.dockerignore`.
- No secrets exist in the Dockerfile.
- No secrets exist in the image build logs.
- The image does not contain local databases.
- The app uses production server software where appropriate.
- Dependency files are intentional and reviewed.
- Unnecessary OS packages are not installed.
- Debug mode is disabled in production.
- Production environment variables are set by the host platform.
- The app binds to `0.0.0.0` inside the container.
- Volumes are used for persistent local data.
- Production data is stored in managed services or durable infrastructure.

For Flask specifically:

- Use Gunicorn in production.
- Set `FLASK_ENV=production` in production.
- Set a strong `SECRET_KEY`.
- Use HTTPS behind the deployment platform or reverse proxy.
- Keep OAuth redirect URLs aligned with the deployed domain.
- Do not use SQLite for serious production workloads.

## Common Mistakes

Mistake:

```text
The app works locally but not in Docker.
```

Likely causes:

- Missing system dependency.
- App binds to `127.0.0.1`.
- Wrong startup command.
- Missing environment variable.
- Required file excluded by `.dockerignore`.

Mistake:

```text
The database resets every time.
```

Likely cause:

- No volume is configured.

Mistake:

```text
Secrets are inside the image.
```

Likely causes:

- `.env` was copied.
- Secret was written in the Dockerfile.
- Secret was passed as a build argument.

Mistake:

```text
Docker build is slow every time.
```

Likely causes:

- Dependency installation happens after copying all source files.
- `.dockerignore` is missing or weak.
- Large unnecessary files are included in the build context.

Mistake:

```text
The container exits immediately.
```

Likely causes:

- Startup command fails.
- App crashes on missing config.
- Process runs and exits instead of staying alive.

## How To Review AI-Generated Docker Files

Ask these questions:

- Does the Dockerfile use the correct language/runtime version?
- Does the command actually start my app?
- Is it using a production server?
- Are secrets excluded?
- Does the `.dockerignore` make sense?
- Are dependencies installed efficiently?
- Are unnecessary packages included?
- Is the port correct?
- Is Compose meant for dev, production, or both?
- Are volumes used only where needed?
- Can another developer run this with only Docker installed?

AI is useful for:

- Explaining Docker files.
- Spotting security issues.
- Improving caching.
- Debugging startup failures.
- Writing Compose files.
- Translating local setup steps into Docker steps.

AI should not be used as blind autopilot for shipping infrastructure.

## Practical Learning Plan

Do not watch another long Docker course right now unless you are blocked.

Instead:

```text
1. Dockerize one project.
2. Run it locally.
3. Break the startup command and fix it.
4. Break the port mapping and fix it.
5. Add a database service.
6. Run tests inside Docker.
7. Push the image to a registry.
8. Deploy it.
9. Repeat on another project.
```

Learn by debugging specific problems.

Search or watch short explanations only when you hit a concrete question.

## Recommended Methodology For Engineering

Use this decision process:

```text
Can docker init generate a useful starting point?
Yes -> use it, then review and edit.
No -> write a Dockerfile manually.

Does the app need multiple services locally?
Yes -> use Compose.
No -> Dockerfile may be enough.

Does the app need persistent data locally?
Yes -> use a named volume.
No -> keep containers disposable.

Does production need a database?
Yes -> use a managed database unless you have a reason not to.

Are secrets involved?
Yes -> runtime env vars only.

Is this production?
Yes -> no debug server, no reload mode, no baked secrets.
```

The final engineering standard:

```text
Docker files should be simple enough to explain,
secure enough to ship,
and boring enough to maintain.
```

## Final Checklist Before Committing Docker Support

Run:

```bash
docker compose up --build
```

Check:

- App starts successfully.
- App is reachable in the browser.
- Logs are clean enough to understand.
- `.env` is not copied into the image.
- Docker files are committed.
- `.env` remains uncommitted.
- README includes the Docker run command.

Optional but useful:

```bash
docker compose run --rm web pytest
```

If all of that passes, the Docker setup is good enough to keep.

