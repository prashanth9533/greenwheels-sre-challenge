# Greenwheels Fleet Lease Service --- SRE Engineering Challenge

> **Status: In progress.** This repository is being built in phases.
> Items described as planned are not implemented until verified.

## 1. Project overview

Greenwheels is an electric-mobility company operating across Kenya,
Ghana, and Uganda. Its fleet operations platform manages driver lease
agreements, payment cycles, and vehicle assignments.

This project builds a production-minded Site Reliability Engineering
(SRE) foundation for a simulated Fleet Lease Service. The objective is
to make the service observable, measurable, operable during incidents,
and safer to deploy---not just to create an API.

## 2. Objectives

-   Build a Python API for lease retrieval and lease event ingestion.
-   Persist lease facts and process events asynchronously.
-   Emit structured JSON logs with request ID, driver ID, event type,
    and latency.
-   Define meaningful SLIs, SLOs, and error budgets.
-   Provide dashboards and actionable alerts with runbook links.
-   Document incident response and an on-call model.
-   Automate linting, tests, image publishing, and a health-check
    reliability gate.
-   Explain how the service could scale to the challenge workload.

## 3. Planned architecture

``` text
Clients
   |
   v
FastAPI Fleet Lease API ------> /health
   |                           /metrics
   v
Lease domain logic
   |
   +------> PostgreSQL (lease facts / persistence)
   |
   +------> Kafka (event streaming)
                  |
                  v
             Event worker

Prometheus ------> Grafana dashboards
     |
     +-----------> Alert rules / on-call

GitHub Actions --> lint / tests / image build
Terraform -------> AWS observability resources
```

The final implementation will separate routing, domain logic,
persistence, and background processing. The event persistence design
should avoid unsafe PostgreSQL/Kafka dual writes; a transactional outbox
and idempotent consumer are the intended reliability pattern.

## 4. API endpoints

  -----------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- -----------------------
  GET                     `/health`               Liveness/readiness
                                                  health check

  GET                     `/leases/{driver_id}`   Retrieve lease status
                                                  and payment cycle

  POST                    `/leases/events`        Accept a lease fact
                                                  (payment made, missed,
                                                  or paused)

  GET                     `/metrics`              Prometheus-compatible
                                                  metrics
  -----------------------------------------------------------------------

## 5. Observability and SLO plan

The service will expose at least three useful SLIs:

1.  Request success rate / error rate.
2.  API request latency, including p95 latency.
3.  Lease event processing time.

Each SLO will document its target, measurement window, measurement
method, and error budget. Targets are engineering assumptions for this
exercise, not existing Greenwheels production commitments.

Planned telemetry includes structured JSON logs and Prometheus metrics
for request volume, errors, duration, event processing, and Kafka
consumer lag.

Prometheus alert rules and Grafana dashboards will be stored as code. At
least three actionable alerts will cover: - High error rate on
`POST /leases/events`. - API latency SLO breach. - Service health check
failure.

Each alert will specify a condition, severity, runbook reference, and
notification channel.

## 6. Incident response and on-call

`RUNBOOK.md` will cover: - **Lease event processing backlog:** Kafka
consumer lag rises and payment events are not processed. - **Database
connection pool exhaustion:** RDS connections are exhausted and lease
endpoints return HTTP 500 errors.

`ONCALL.md` will describe a four-engineer rotation covering Nairobi
(UTC+3) and Pune (UTC+5:30), including handoffs, escalation,
error-budget-based deployment decisions, and a 90-day alert-fatigue
reduction plan.

## 7. Scale design

`ARCHITECTURE.md` will address the challenge scenario: - 500,000
registered drivers across 8 countries. - 50,000 active leases with daily
payment events. - Peak ingestion of 500 lease events per second. -
Degraded RDS read latency during peak processing. - Kafka consumer lag
during deployment rollout.

The design will cover Kafka partitioning and consumer groups, database
read replicas, caching and invalidation, lag detection and recovery,
safe ECS rolling deployments, and AWS cost optimization.

## 8. Technology stack

  Area                Technology
  ------------------- --------------------------
  API                 Python, FastAPI, Uvicorn
  Database            PostgreSQL
  Event streaming     Apache Kafka
  Metrics             Prometheus
  Dashboards          Grafana
  Containers          Docker, Docker Compose
  Cloud / IaC         AWS, Terraform
  CI/CD               GitHub Actions
  Testing / quality   pytest, HTTPX, Ruff

## 9. Repository structure

``` text
.
├── app/
│   ├── api/             # HTTP routes
│   ├── domain/          # Lease business logic
│   ├── persistence/     # Database access
│   └── worker/          # Background event consumer
├── infra/               # Terraform definitions
├── monitoring/
│   ├── prometheus/      # Scrape and alert rules
│   └── grafana/         # Dashboard provisioning
├── tests/               # Unit and integration tests
├── .github/workflows/   # CI/CD workflow
├── ARCHITECTURE.md
├── AI_USAGE.md
├── ONCALL.md
├── RUNBOOK.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 10. Local setup

### Prerequisites

-   Git
-   Python 3.12 or another supported compatible version
-   Docker Desktop with Docker Compose
-   Terraform for infrastructure validation

### Clone the repository

``` bash
git clone <your-repository-url>
cd greenwheels-sre-challenge
```

### Create and activate a virtual environment

Windows PowerShell:

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Start the stack

Once the application and Compose configuration are complete:

``` bash
docker compose up --build
```

Run in the background:

``` bash
docker compose up --build -d
```

Stop the stack:

``` bash
docker compose down
```

View logs:

``` bash
docker compose logs -f
```

### Verify the service

After startup, use the API port configured in `docker-compose.yml`:

``` bash
curl http://localhost:<api-port>/health
curl http://localhost:<api-port>/metrics
```

Replace `<api-port>` with the verified configured port before final
submission. Add sample successful responses after implementation.

## 11. Tests and lint

``` bash
pytest -v
ruff check .
```

Tests will cover lease event ingestion, SLI calculation, and an
integration check that validates the expected SLI metric labels on
`/metrics`.

## 12. CI/CD and infrastructure

The planned GitHub Actions workflow will run lint and unit tests on pull
requests, build and push the Docker image when changes are merged to
`main`, then verify that `/health` returns HTTP 200 within 10 seconds
after container startup. Failure to pass this health check must fail the
workflow.

Terraform will define at least a CloudWatch log group, metric filters,
and two CloudWatch alarms. Prometheus/Grafana configuration will provide
the local observability path.

## 13. What an evaluator should observe

After implementation, an evaluator should be able to: - Start the stack
with one Docker Compose command. - Call the health, lease retrieval, and
event ingestion endpoints. - Inspect structured JSON logs. - Scrape
`/metrics` and review the defined SLIs. - Inspect Grafana dashboards and
alert definitions. - Follow the two incident runbooks. - Review the
on-call model and scale design. - Validate Terraform and run the tests
and lint checks.

## 14. Assumptions and known limitations

-   This is a simulated challenge, not a connection to Greenwheels
    production systems.
-   SLO targets, alert thresholds, retention periods, and resource sizes
    are engineering assumptions to be tuned with real traffic data.
-   AWS deployment requires an AWS account, credentials, and
    environment-specific configuration. Never commit credentials or
    secrets.
-   Slack notifications require a configured integration or webhook;
    secrets must not be stored in source control.
-   Local Docker Compose is for development and demonstration, not a
    production deployment topology.
-   Planned features must not be represented as completed until their
    implementation and validation are demonstrated.

## 15. Interview explanation (60--90 seconds)

"I worked on an SRE engineering challenge for a simulated
electric-mobility fleet lease platform. The service manages driver lease
information and payment-related events. My objective was to establish a
reliability foundation around the service, not just develop an API.

I designed the service around Python and FastAPI, PostgreSQL for
persistence, and Kafka for asynchronous event processing. I separated
the API layer, business logic, persistence, and worker responsibilities
so that each part can be maintained and scaled independently.

From an SRE perspective, I focused on business-relevant SLIs such as
request success rate, API latency, and lease event processing time. I
defined the approach for SLOs and error budgets, and planned Prometheus
metrics, Grafana dashboards, and actionable alerts linked to runbooks.

I also documented incident response for Kafka consumer backlog and
database connection pool exhaustion, and designed an on-call model for
engineers in Nairobi and Pune. For delivery, I included Terraform for
AWS observability resources and GitHub Actions for linting, testing,
image publishing, and a health-check reliability gate.

Finally, I considered how the service could scale to 500,000 drivers and
500 events per second, including Kafka partitioning, read replicas,
caching, safe deployments, and cost optimization."

**Important:** The repository is still being implemented phase by phase.
Until a feature is coded and tested, describe it in interviews as a
design or implementation plan---not as a completed production feature.
Update this explanation as each phase is validated.

## 16. Evaluation priorities

  Area                                   Weight
  ------------------------------------ --------
  Observability and SLO design              30%
  Incident runbook quality                  20%
  Infrastructure as Code                    15%
  Service implementation and testing        15%
  Scale exercise                            10%
  CI/CD and reliability gate                 5%
  Communication and documentation            5%

The challenge emphasizes clarity, correctness, operational thinking, and
polish.
