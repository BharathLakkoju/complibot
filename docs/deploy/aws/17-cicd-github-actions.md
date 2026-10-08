# Step 17 — GitHub Actions CI/CD

**Goal:** On merge to `master`, test, build image, push ECR, deploy ECS, run migrations.

## 17.1 Create workflow file

Add `.github/workflows/deploy-demo.yml` (example skeleton):

```yaml
name: Deploy demo

on:
  push:
    branches: [master]

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: complibot
  ECS_CLUSTER: complibot-demo
  ECS_SERVICE_API: complibot-api
  ECS_SERVICE_WORKER: complibot-worker

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --all-extras
      - run: uv run pytest -q
        env:
          PYTHONPATH: packages/complibot/src

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - uses: aws-actions/amazon-ecr-login@v2
      - id: build
        run: |
          IMAGE=${{ steps.login.outputs.registry }}/${{ env.ECR_REPOSITORY }}
          docker build -t $IMAGE:${{ github.sha }} -t $IMAGE:latest .
          docker push $IMAGE:${{ github.sha }}
          docker push $IMAGE:latest

      - name: Run migrations
        run: |
          aws ecs run-task ... # complibot-migrate task definition

      - name: Deploy API
        run: |
          aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE_API --force-new-deployment

      - name: Deploy worker
        run: |
          aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE_WORKER --force-new-deployment
```

Fill in `run-task` networking from your VPC/subnets/SG.

## 17.2 GitHub repository settings

**Settings** → **Actions** → **General**:

- **Workflow permissions:** Read and write (if pushing artifacts).
- **Allow GitHub Actions to create and approve pull requests:** off unless needed.

**Variables** (from step 03):

- `AWS_ROLE_ARN`
- `AWS_REGION`

## 17.3 PR pipeline (lighter)

Separate workflow on `pull_request`:

- `pytest`, `ruff`, `pnpm typecheck` in `apps/web`
- `terraform plan` comment (when modules exist)
- Eval smoke gate when `packages/complibot` pipeline changes (future)

## 17.4 Immutable tags

Always deploy `:${{ github.sha }}`, not only `:latest`, so rollback is one tag change.

## Verification

- Push to `master` triggers workflow green.
- ECS services show new deployment with new task definition revision.
- Health check passes.

## Next step

→ [18-cost-scale-down.md](18-cost-scale-down.md)
