# aws-qa-learning

Personal learning project for AWS testing patterns using LocalStack as an emulator. Part of a structured QA Automation Engineer skill development plan.

## Stack

- Python 3.12 (managed via `uv`)
- LocalStack (Docker Compose) — S3, SQS, SNS, DynamoDB, Lambda, IAM, STS, Logs, EventBridge, Step Functions
- pytest + boto3
- AWS CLI + awslocal
- ruff (lint/format), taskipy (task runner)

## Setup

1. **LocalStack auth token**: Set `LOCALSTACK_AUTH_TOKEN` env var (get from app.localstack.cloud, free Hobby plan)
2. **Start LocalStack**: `docker compose up -d`
3. **Activate venv**: `.venv\Scripts\activate`
4. **Run tests**: `pytest -v`

## Structure

```text
aws-qa-learning/
├── lambdas/                    # Lambda handlers
├── src/
│   └── aws_qa_learning/
│       ├── helpers/            # S3, SQS, and DynamoDB helper functions
│       ├── aws_clients.py      # Centralized boto3 client factories pointed at LocalStack
│       └── utils.py            # Shared test utilities 
├── tests/                      # Learning exercises
│   ├── dynamodb
│   ├── integration
│   ├── lambda
│   ├── s3
│   ├── sns
│   ├── sqs
│   ├── conftest.py
│   └── factories.py
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Learning Phases

- [x] Phase 1: S3 + boto3 fundamentals
- [x] Phase 2: Messaging (SQS, SNS)
- [x] Phase 3: State & Compute (DynamoDB, Lambda)
- [x] Phase 4: Integration (Step Functions, EventBridge)
