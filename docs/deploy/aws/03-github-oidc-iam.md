# Step 03 — GitHub OIDC and deploy IAM role

**Goal:** Let **GitHub Actions** deploy to AWS **without** long-lived access keys.

**Trust:** only repo `BharathLakkoju/complibot`, branch `master` (adjust if you use `main`).

## 3.1 Create OIDC identity provider

1. Console search: **IAM**.
2. Left: **Identity providers**.
3. Click **Add provider**.
4. **Provider type:** **OpenID Connect**.
5. **Provider URL:** `https://token.actions.githubusercontent.com`
6. Click **Get thumbprint** (should succeed).
7. **Audience:** `sts.amazonaws.com`
8. Click **Add provider**.

## 3.2 Create IAM role for GitHub Actions

1. IAM → **Roles** → **Create role**.
2. **Trusted entity type:** **Web identity**.
3. **Identity provider:** `token.actions.githubusercontent.com`.
4. **Audience:** `sts.amazonaws.com`.
5. Click **Next** (permissions — add policies in a moment).

### Trust policy (customize on review screen)

After creation you will edit trust to restrict by repo. Example trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:BharathLakkoju/complibot:ref:refs/heads/master"
        }
      }
    }
  ]
}
```

Replace `YOUR_ACCOUNT_ID`. If your default branch is `main`, change `refs/heads/master` to `refs/heads/main`.

**Console path to edit trust:**

1. **Roles** → click role → **Trust relationships** → **Edit trust policy** → paste → **Update policy**.

### Permissions (demo — tighten later)

Attach policies (or one custom policy) allowing:

| Service | Actions (summary) |
|---------|-------------------|
| ECR | push/pull images |
| ECS | update service, register task definition, run task |
| IAM | pass role to ECS tasks (scoped) |
| S3 | terraform state bucket only |
| Terraform resources | as needed when you apply modules |

For first learning deploy, teams often attach **PowerUserAccess** temporarily; **do not** use AdministratorAccess in CI for long term.

**Role name:** `complibot-github-deploy-demo`

6. **Create role**.
7. Copy **Role ARN** → scratch pad (used in GitHub Actions secrets/vars).

## 3.3 Configure GitHub repository

1. Open `https://github.com/BharathLakkoju/complibot`.
2. **Settings** → **Secrets and variables** → **Actions**.

### Repository variables (preferred for non-secret)

| Name | Value |
|------|--------|
| `AWS_REGION` | `us-east-1` |
| `AWS_ROLE_ARN` | ARN of `complibot-github-deploy-demo` |

### No static keys

Do **not** add `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` if using OIDC.

Workflow snippet (see [17-cicd-github-actions.md](17-cicd-github-actions.md)):

```yaml
permissions:
  id-token: write
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ vars.AWS_ROLE_ARN }}
      aws-region: ${{ vars.AWS_REGION }}
```

## Verification

- IAM → **Roles** → `complibot-github-deploy-demo` → **Trust relationships** shows GitHub OIDC.
- GitHub repo variables show `AWS_ROLE_ARN`.

## Next step

→ [04-terraform-state-bootstrap.md](04-terraform-state-bootstrap.md)
