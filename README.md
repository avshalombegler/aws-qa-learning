# aws-qa-learning

Personal learning project for AWS testing patterns using LocalStack as an emulator. Part of a structured QA Automation Engineer skill development plan.

## Stack

- Python 3.12 (managed via `uv`)
- LocalStack (Docker Compose)
- pytest + boto3
- AWS CLI + awslocal

## Setup

1. **LocalStack auth token**: Set `LOCALSTACK_AUTH_TOKEN` env var (get from app.localstack.cloud, free Hobby plan)
2. **Start LocalStack**: `docker compose up -d`
3. **Activate venv**: `.venv\Scripts\activate`
4. **Run tests**: `pytest -v`

## Structure

- `src/aws_qa_learning/` - reusable helpers and fixtures
- `tests/` - learning exercises and pattern demonstrations
- `docs/notes.md` - inline learning notes

## Learning Phases

- [ ] Phase 1: S3 + boto3 fundamentals
- [ ] Phase 2: Messaging (SQS, SNS)
- [ ] Phase 3: State & Compute (DynamoDB, Lambda)
- [ ] Phase 4: Integration (Step Functions, EventBridge)
- [ ] Phase 5: Portfolio integration with seleniumbase-python
