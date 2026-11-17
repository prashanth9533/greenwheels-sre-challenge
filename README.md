

# Greenwheels Fleet Lease Service — SRE Engineering Challenge
> **Status: Done.** The core challenge implementation and documentation are complete, including the FastAPI service, PostgreSQL persistence, Kafka event-processing components, observability configuration, Terraform resources, CI/CD workflow, tests, and operational documentation. Final Docker Compose integration and end-to-end verification remain outstanding; see [Assumptions and known limitations](#14-assumptions-and-known-limitations).



## 1. Project overview
Greenwheels is a simulated electric-mobility company operating across Kenya, Ghana, and Uganda. Its fleet operations platform manages driver lease agreements, payment cycles, and vehicle assignments.



This project establishes a production-minded Site Reliability Engineering (SRE) foundation for a simulated Fleet Lease Service. The focus is on service reliability, observability, incident response, safe delivery, and scalability—not only API development.



## 2. Objectives
- Provide an API for lease retrieval and lease-event ingestion.

- Persist lease facts and process events asynchronously.

- Emit structured JSON logs containing request IDs, driver IDs, event types, and latency.

- Define service-level indicators (SLIs), service-level objectives (SLOs), and error-budget concepts.

- Provide Prometheus metrics, Grafana dashboard provisioning, and actionable alert rules.

- Document incident response and an on-call operating model.

- Automate linting, tests, Docker image publishing, and a health-check reliability gate.

- Describe how the service could scale to the challenge workload.



## 3. Architecture
```text

                         Clients

                            |

                            v

                  FastAPI Fleet Lease API

                     /health /metrics

                            |

                            v

                     Lease domain logic

                       /          \\

                      v            v

                 PostgreSQL      Outbox table

                                    |

                                    v

                             Outbox publisher

                                    |

                                    v

                                  Kafka

                                    |

                                    v

                              Kafka consumer

                                    |

                                    v

                         Idempotent event record



       Prometheus ------> FastAPI and consumer metrics

            |

            v

       Grafana dashboards



       Prometheus alert rules ------> Alertmanager ------> Email



       GitHub Actions ------> lint / tests / Docker build / GHCR publish

       Terraform -----------> AWS CloudWatch observability resources

```



The service separates routing, domain logic, persistence, and background processing. The transactional outbox pattern is used to avoid directly coupling a database transaction to Kafka publishing. The consumer uses idempotency records to avoid applying duplicate events.



## 4. API endpoints
| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/health` | Service health check |

| GET | `/leases/{driver_id}` | Retrieve lease status and payment-cycle information |

| POST | `/leases/events` | Accept a lease event, such as payment made, missed, or paused |

| GET | `/metrics` | Expose Prometheus-compatible metrics |



## 5. Observability and SLOs
The implementation includes three service-level measurement areas:



1. ****Request success/error rate**** — tracks API request outcomes.

2. ****API latency**** — measures request duration and supports p95 latency analysis.

3. ****Lease event processing time**** — measures event-processing performance.



SLO targets, measurement windows, and error budgets are engineering assumptions for this exercise; they are not existing Greenwheels production commitments.



Structured JSON logs include request context such as request ID, driver ID, event type, and latency. Prometheus configuration scrapes the API and Kafka-consumer metrics. Grafana dashboard provisioning and Prometheus alert rules are stored in the repository.



The alert configuration covers:

- High lease-event API error rate.

- API latency SLO breach.

- FastAPI service health failure.



Alerts include severity and operational context, including runbook references. Alertmanager is configured for email notifications.



## 6. Incident response and on-call
Operational guidance is documented in:



- ****`RUNBOOK.md`**** — troubleshooting Kafka consumer lag/event backlog and database connection-pool exhaustion affecting lease API requests.

- ****`ONCALL.md`**** — a four-engineer rotation across Nairobi (UTC+3) and Pune (UTC+5:30), including handoffs, escalation, error-budget deployment decisions, and a 90-day alert-fatigue reduction plan.



## 7. Scale design
`ARCHITECTURE.md` addresses the challenge scenario:



- 500,000 registered drivers across 8 countries.

- 50,000 active leases.

- Peak ingestion of 500 lease events per second.

- Degraded RDS read latency during peak processing.

- Kafka consumer lag during deployment rollout.



The design discusses Kafka partitioning and consumer groups, database read replicas, caching and invalidation, lag detection and recovery, safe ECS rolling deployments, and AWS cost optimization. These are architecture recommendations for the scale exercise, not a claim that a production-scale AWS environment has been deployed.



## 8. Technology stack
| Area | Technology |

|---|---|

| API | Python, FastAPI, Uvicorn |

| Database | PostgreSQL, SQLAlchemy |

| Event streaming | Apache Kafka |

| Metrics | Prometheus |

| Dashboards | Grafana |

| Alerting | Prometheus alert rules, Alertmanager, email |

| Containers | Docker, Docker Compose |

| Cloud / IaC | AWS, Terraform |

| CI/CD | GitHub Actions, GitHub Container Registry |

| Testing / quality | pytest, HTTPX, Ruff |



## 9. Repository structure
```text

.

├── app/

│   ├── api/                 # HTTP routes

│   ├── domain/              # Lease business logic

│   ├── observability/       # SLI and observability logic

│   ├── persistence/         # Database access and models

│   └── worker/              # Outbox publisher and Kafka consumer

├── infra/                   # Terraform definitions

├── monitoring/

│   ├── alertmanager/        # Alertmanager configuration

│   ├── grafana/             # Dashboard and provisioning configuration

│   └── prometheus/          # Scrape configuration and alert rules

├── tests/                   # Unit and API tests

├── .github/workflows/       # CI/CD workflow

├── ARCHITECTURE.md

├── AI_USAGE.md

├── ONCALL.md

├── RUNBOOK.md

├── Dockerfile

├── docker-compose.yml

└── requirements.txt

```



## 10. Local setup
### Prerequisites
- Git

- Python 3.13 (the Docker image uses Python 3.13)

- Docker Desktop with Docker Compose

- Terraform, if validating the infrastructure configuration



### Clone the repository
```bash

git clone https://github.com/prashanth9533/greenwheels-sre-challenge.git

cd greenwheels-sre-challenge

```



### Create and activate a virtual environment
Windows PowerShell:



```powershell

python -m venv .venv

.\.venv\Scripts\Activate.ps1

```



Linux / macOS:



```bash

python3 -m venv .venv

source .venv/bin/activate

```



### Install dependencies
```bash

python -m pip install --upgrade pip

pip install -r requirements.txt

```



### Run tests and lint locally
```bash

python -m pytest -q

python -m ruff check .

```



Latest local verification recorded during development: ****15 tests passed**** and ****Ruff checks passed****. A Starlette/httpx deprecation warning was reported by the test environment; it did not fail the test run.



### Docker Compose
The Compose file currently starts the supporting infrastructure services: PostgreSQL, Kafka, Prometheus, Grafana, and Alertmanager. The API and worker services are being integrated into the Compose stack and must pass end-to-end verification before the complete-stack command is treated as the final one-command demo.



To start the currently configured Compose services:



```bash

docker compose up -d

```



To inspect service status and logs:



```bash

docker compose ps

docker compose logs -f

```



To stop the Compose-managed services:



```bash

docker compose down

```



****Data note:**** `docker compose down` does not remove named volumes. Do not use `docker compose down -v` unless you intentionally want to delete the local PostgreSQL, Kafka, and Grafana data volumes.



### API verification
A separately started development API container was verified on host port `8002` during development:



```bash

curl http://localhost:8002/health

curl http://localhost:8002/metrics

```



Use the port configured for the API instance you have actually started. The planned Compose-managed API port is `8003`, subject to final Compose integration and verification.



## 11. Tests and code quality
Run:



```bash

python -m pytest -v

python -m ruff check .

```



The test suite covers lease-service/API behavior and SLI calculations. The API metrics endpoint is included in the tests. The local test run completed with 15 passing tests.



## 12. CI/CD and infrastructure
### GitHub Actions
The GitHub Actions workflow runs on pull requests and pushes to `main`. It performs linting and automated tests, builds the Docker image, runs a container health check, and publishes the image to GitHub Container Registry on pushes to `main`.



- ****Repository:**** https://github.com/prashanth9533/greenwheels-sre-challenge

- ****Actions:**** https://github.com/prashanth9533/greenwheels-sre-challenge/actions

- ****Container image:**** `ghcr.io/prashanth9533/greenwheels-sre-challenge:latest`



The workflow has completed successfully during project validation.



### Terraform / AWS
The Terraform configuration provisions:

- A CloudWatch log group with retention configuration.

- CloudWatch metric filters for application errors and request latency.

- Two CloudWatch alarms.



The Terraform apply completed successfully during development. AWS resources may incur charges while they remain deployed. Review the resources and cost implications before leaving them running.



## 13. What an evaluator can review
An evaluator can review:



- The FastAPI health, lease retrieval, and event-ingestion endpoints.

- Structured application logging and Prometheus metrics.

- SLI calculation logic and automated tests.

- Prometheus scrape and alert configuration.

- Grafana dashboard provisioning and Alertmanager configuration.

- The Kafka outbox publisher and idempotent consumer implementation.

- The incident runbooks and on-call operating model.

- The scale-design document.

- Terraform definitions and GitHub Actions workflow.

- The published Docker image in GHCR.



The complete Docker Compose application-and-worker integration and end-to-end event flow remain subject to final verification.



## 14. Assumptions and known limitations
- This is a simulated challenge, not a connection to Greenwheels production systems.

- SLO targets, alert thresholds, retention periods, and resource sizes are engineering assumptions to be tuned using real traffic data.

- AWS deployment requires an AWS account and environment-specific configuration. Never commit credentials or secrets.

- The Terraform resources provision observability components; they do not constitute a complete production application deployment.

- The scale exercise describes a proposed architecture; it does not deploy a production environment for 500,000 drivers.

- Local Docker Compose is for development and demonstration, not a production deployment topology.

- The Kafka consumer has idempotency handling. A production deployment should additionally implement and validate a complete dead-letter queue, retry policy, schema evolution strategy, and operational recovery process.

- Final Docker Compose integration and full end-to-end validation of API-to-outbox-to-Kafka-to-consumer processing are still pending.

- Do not represent a feature as production-ready solely because its configuration or design document exists; verify its runtime behavior.



## 15. Evaluation priorities
| Area | Weight |

|---|---:|

| Observability and SLO design | 30% |

| Incident runbook quality | 20% |

| Infrastructure as Code | 15% |

| Service implementation and testing | 15% |

| Scale exercise | 10% |

| CI/CD and reliability gate | 5% |

| Communication and documentation | 5% |



The challenge emphasizes clarity, correctness, operational thinking, and polish.
