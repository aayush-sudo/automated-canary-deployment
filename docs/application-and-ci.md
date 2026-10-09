# Application and CI Documentation

## 1. Overview

The canary-demo application is a small Flask-based HTTP API developed for the DevOps IA2 project.

It supports two application versions, v1 and v2. The application version is selected using the APP_VERSION environment variable.

The application is intended to be deployed to Kubernetes and used in a progressive delivery demonstration involving Flagger and Istio.

## 2. Technology Stack

- Python 3.13
- Flask
- Pytest
- Docker
- GitHub Actions
- Kubernetes and Minikube for deployment

## 3. Application Structure

    app/
    ├── app.py
    ├── test_app.py
    ├── requirements.txt
    └── Dockerfile

    .github/
    └── workflows/
        └── ci.yml

    docs/
    └── application-and-ci.md

## 4. API Endpoints

The application listens on port 5001 by default.

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | / | Returns the application name, version, and welcome message |
| GET | /health | Returns the application's health status |
| GET | /version | Returns the running application version |

Successful requests return HTTP 200.

### Example: Health Response

    {
      "status": "healthy",
      "application": "canary-demo",
      "version": "v1"
    }

### Example: Version Response

    {
      "application": "canary-demo",
      "version": "v2"
    }

## 5. Local Setup

From the repository root, create and activate a Python virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install -r app/requirements.txt

## 6. Run the Application Locally

Run v1:

    python app/app.py

The default version is v1, and the default port is 5001.

Run v2:

    APP_VERSION=v2 python app/app.py

To select another port, set the PORT environment variable:

    PORT=5002 python app/app.py

Test the endpoints:

    curl http://127.0.0.1:5001/
    curl http://127.0.0.1:5001/health
    curl http://127.0.0.1:5001/version

## 7. Automated Tests

Run the test suite from the repository root:

    python -m pytest app/test_app.py -v

The tests cover the home, health, and version endpoints for v1 and v2.

The current test suite contains six tests.

## 8. Docker Images

Build the v1 image:

    docker build -f app/Dockerfile -t canary-demo:v1 app/

Build the v2 image:

    docker build -f app/Dockerfile -t canary-demo:v2 app/

List the images:

    docker images canary-demo

Both images use the same application code. APP_VERSION selects which version the running container reports.

## 9. Run the Docker Containers

Run v1:

    docker run -d --name canary-v1 \
      -p 5001:5001 \
      -e APP_VERSION=v1 \
      canary-demo:v1

Run v2:

    docker run -d --name canary-v2 \
      -p 5001:5001 \
      -e APP_VERSION=v2 \
      canary-demo:v2

Only one of these example containers should use host port 5001 at a time.

Check a running container:

    docker ps
    docker logs canary-v1

Stop and remove the container when finished:

    docker stop canary-v1
    docker rm canary-v1

Use the corresponding container name when testing v2.

## 10. GitHub Actions CI

Workflow file:

    .github/workflows/ci.yml

The workflow runs on pushes to main and feature branches, and on pull requests targeting main.

The pipeline:

1. Checks out the repository.
2. Sets up Python 3.13.
3. Installs dependencies.
4. Runs the automated tests.
5. Builds the v1 Docker image.
6. Builds the v2 Docker image.

The workflow builds images for validation but does not publish them to a container registry.

To inspect a workflow run, open the repository on GitHub and select Actions.

## 11. Kubernetes and Minikube Handoff

The container port is 5001.

The Kubernetes container configuration should use:

- Container port: 5001
- Application health endpoint: /health
- Version endpoint: /version
- Image tags: canary-demo:v1 and canary-demo:v2

For local Minikube deployment, the images must be available to the Minikube cluster.

After confirming the intended Minikube profile, load each image:

    minikube image load canary-demo:v1
    minikube image load canary-demo:v2

If using a different Minikube profile, specify the correct profile when loading the images.

When using these locally loaded images in Kubernetes manifests, configure the appropriate imagePullPolicy, such as IfNotPresent, so Kubernetes can use the local image.

The final integration operator should verify the active Kubernetes context and Minikube profile before deployment.

## 12. Important Implementation Notes

- APP_VERSION selects the reported application version.
- PORT controls the application listening port; its default is 5001.
- The health endpoint is a basic application-response check, not a comprehensive dependency check.
- The current CI workflow does not publish Docker images.
- Local Docker images are not automatically shared with another developer or another Minikube cluster.
- The Flask built-in server is intended for development and demonstration, not production deployment.
