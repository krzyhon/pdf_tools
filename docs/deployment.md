# Deployment Guide

## Prerequisites

- AWS account with programmatic access
- Terraform >= 1.10
- Docker
- AWS CLI v2
- GitHub repository with Actions enabled
- Domain managed by an external DNS provider (`flairops.cloud`)

---

## 1. Bootstrap — one-time local setup

### Create the Terraform state bucket

```bash
# Replace <account-id> with your 12-digit AWS account ID
aws s3 mb s3://pdf-tools-tfstate-<account-id> --region eu-west-1

# Enable versioning so you can recover from accidental state corruption
aws s3api put-bucket-versioning \
  --bucket pdf-tools-tfstate-<account-id> \
  --versioning-configuration Status=Enabled
```

State locking uses S3 native locking (`use_lockfile = true`) — no DynamoDB table needed.

### Enable the S3 backend in Terraform

Edit [terraform/main.tf](../terraform/main.tf) and uncomment the backend block:

```hcl
backend "s3" {
  bucket       = "pdf-tools-tfstate-<account-id>"
  key          = "pdf-tools/terraform.tfstate"
  region       = "eu-west-1"
  use_lockfile = true
}
```

---

## 2. First `terraform apply`

```bash
cd terraform
terraform init
terraform apply -var="github_repo=<owner>/<repo>"
```

`terraform apply` will create ~30 resources. It takes about 10–15 minutes because CloudFront distributions take time to propagate.

### After apply — note these outputs

```bash
terraform output
```

| Output | Used for |
|---|---|
| `nameservers` | Add at your external DNS provider (step 3) |
| `github_actions_role_arn` | GitHub secret `AWS_DEPLOY_ROLE_ARN` |
| `terraform_role_arn` | GitHub secret `AWS_TERRAFORM_ROLE_ARN` |
| `frontend_bucket` | GitHub secret `FRONTEND_BUCKET` |
| `cloudfront_distribution_id` | GitHub secret `CF_DISTRIBUTION_ID` |
| `ecr_repository_url` | Reference for manual Docker pushes |

---

## 3. Delegate the subdomain

At your external DNS provider, add **4 NS records** for `pdftools.flairops.cloud` pointing to the nameservers from the output above. This is a one-time step — the records never change.

```
pdftools.flairops.cloud  NS  ns-xxx.awsdns-xx.com
pdftools.flairops.cloud  NS  ns-yyy.awsdns-yy.org
pdftools.flairops.cloud  NS  ns-zzz.awsdns-zz.co.uk
pdftools.flairops.cloud  NS  ns-www.awsdns-ww.net
```

DNS propagation takes a few minutes to a few hours. ACM certificate validation completes automatically once Route53 can see the DNS records.

---

## 4. Configure GitHub secrets

In your repository: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | From `terraform output github_actions_role_arn` |
| `AWS_TERRAFORM_ROLE_ARN` | From `terraform output terraform_role_arn` |
| `FRONTEND_BUCKET` | From `terraform output frontend_bucket` |
| `CF_DISTRIBUTION_ID` | From `terraform output cloudfront_distribution_id` |
| `TF_STATE_BUCKET` | `pdf-tools-tfstate-<account-id>` |

---

## 5. First application deployment

Push to `main` to trigger the deploy pipeline:

```bash
git push origin main
```

The pipeline will:
1. Build the Docker image and push it to ECR
2. Force a new ECS deployment and wait for health checks to pass
3. Sync `frontend/` to S3 and invalidate the CloudFront cache

The site will be live at `https://pdftools.flairops.cloud` once the ECS tasks are healthy (~2–3 minutes after the push).

---

## CI/CD Workflows

### On every pull request

| Workflow | What it does |
|---|---|
| `tests.yml` | Ruff lint, mypy, pip-audit, pytest with coverage ≥ 80% |
| `terraform.yml` | `fmt -check`, `validate`, `plan` — posts the plan as a PR comment |

Both must pass before a PR can be merged (configure branch protection in repository settings).

### On every push to `main`

| Workflow | What it does |
|---|---|
| `deploy.yml` (backend) | `docker build` → push `:sha` + `:latest` to ECR → `ecs update-service --force-new-deployment` → wait for stability |
| `deploy.yml` (frontend) | `aws s3 sync frontend/` → CloudFront invalidation |
| `terraform.yml` | `terraform apply -auto-approve` (no-op if nothing changed) |
| `release.yml` | Bumps a semver tag from Conventional Commits if applicable |

Backend and frontend deploy jobs run in **parallel**.

### Authentication

All workflows use **OIDC** — GitHub exchanges a short-lived token for AWS credentials without any stored access keys. The deploy role can only be assumed from `refs/heads/main`; the Terraform role also allows PRs.

---

## Manual operations

### Force a backend redeployment

```bash
aws ecs update-service \
  --cluster pdf-tools \
  --service pdf-tools \
  --force-new-deployment \
  --region eu-west-1
```

### Rebuild and push the Docker image manually

```bash
# Log in to ECR
aws ecr get-login-password --region eu-west-1 \
  | docker login --username AWS --password-stdin \
    $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-1.amazonaws.com

ECR=$(terraform -chdir=terraform output -raw ecr_repository_url)
docker build -t $ECR:latest .
docker push $ECR:latest
```

### Deploy the frontend manually

```bash
BUCKET=$(terraform -chdir=terraform output -raw frontend_bucket)
CF_ID=$(terraform -chdir=terraform output -raw cloudfront_distribution_id)

aws s3 sync frontend/ s3://$BUCKET --delete --cache-control "max-age=3600, must-revalidate"
aws cloudfront create-invalidation --distribution-id $CF_ID --paths "/*"
```

---

## Local development

### Run the API without S3

Set `TEMP_BUCKET` to any existing S3 bucket you have write access to:

```bash
export TEMP_BUCKET=my-dev-bucket
export AWS_REGION=eu-west-1

# Install server dependencies
pip install -r requirements-server.txt

# Start the API
uvicorn app.main:app --reload --port 8000
```

Interactive docs at [http://localhost:8000/api/docs](http://localhost:8000/api/docs).

### Run with Docker

```bash
docker build -t pdf-tools .

docker run \
  -e TEMP_BUCKET=my-dev-bucket \
  -e AWS_REGION=eu-west-1 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -p 8000:8000 \
  pdf-tools
```

### Serve the frontend locally

The frontend fetches `/api/...` relative URLs. To test against the local API, open `frontend/index.html` directly in a browser and change the `fetch` base URL in `app.js`, or proxy requests with a simple server:

```bash
# Using Python's built-in server (no API calls will work, UI only)
cd frontend && python3 -m http.server 3000
```
