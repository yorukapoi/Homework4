## Homework 4 – Crypto Analytics (Refactored & Microservices)

This folder contains the **Homework 4** version of the Crypto Analytics application.

- The original **Homework 3** implementation remains unchanged under `homework3/`.
- This version refactors the analytics layer to use the **Strategy** and **Facade** design patterns.
- It exposes analytics as independent **FastAPI microservices** behind an **API Gateway**.
- All services and the Next.js frontend are **containerized** and can be started with Docker Compose.

For details about the design patterns, microservice responsibilities, and deployment notes,
see `docs/design_and_architecture.md`.


