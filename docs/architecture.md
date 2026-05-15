# Architecture

## Overview

```
                        ┌──────────────────────────────────────────────────────────────┐
                        │                        AWS  eu-west-1                        │
                        │                                                              │
                        │   ┌─────────────┐    /* (static)    ┌──────────────────┐     │
Browser ──HTTPS──▶ CloudFront             │ ──────────────────▶ S3  (frontend)   │     │
  pdftools              │   │ ACM cert    │                   └──────────────────┘     │
  .flairops.cloud       │   │ us-east-1   │    /api/* (proxy)                          │
                        │   └──────┬──────┘ ──────────────────▶ ALB                    │
                        │          │          HTTP + secret      │                     │
                        │          │          header             ▼                     │
                        │          │                       ECS Fargate                 │
                        │          │                       FastAPI app                 │
                        │          │                             │                     │
                        │          │                             ▼                     │
                        │          │                    S3  (temp files)               │
                        │          │                    presigned URLs, 1-day expiry   │
                        │          │                                                   │
                        │   Route53 A/AAAA                  ECR  (Docker images)       │
                        │   → CloudFront                    CloudWatch Logs            │
                        └──────────────────────────────────────────────────────────────┘
```

## Components

### DNS & TLS
| Resource | Detail |
|---|---|
| Route53 hosted zone | Scoped to `pdftools.flairops.cloud` only. The parent zone (`flairops.cloud`) stays at the external provider — add the 4 NS records there once. |
| ACM certificate | Provisioned in `us-east-1` (CloudFront requirement), validated via DNS. |
| CloudFront | Terminates TLS. Serves `/*` from S3 and proxies `/api/*` to the ALB. |

### Network
- **VPC** — `10.0.0.0/16`, two public subnets across two AZs.
- **No NAT Gateway** — ECS tasks run in public subnets with `assignPublicIp: true`. Security groups prevent direct access; only the ALB can reach the tasks.
- **S3 Gateway endpoint** — free; keeps ECS→S3 traffic off the public internet.

### Security: ALB bypass prevention
CloudFront injects a random secret header (`X-CF-Origin-Verify`) on every request. The ALB listener returns **403** by default and only forwards requests that carry this header. Direct ALB access is blocked even though it is on a public IP.

### Backend
| Resource | Detail |
|---|---|
| ECR | Private container registry. Lifecycle policy keeps the last 10 images. Scan on push enabled. |
| ECS Fargate | 0.5 vCPU / 2 GB RAM. Public subnet, no NAT. `desired_count = 1` by default. |
| ALB | Application Load Balancer. HTTP only (CloudFront handles TLS termination). Health check at `GET /api/health`. |

### Storage
| Bucket | Purpose |
|---|---|
| `pdf-tools-frontend-*` | Static frontend files. Private; only CloudFront can read via OAC. |
| `pdf-tools-temp-*` | Processed output files. Private; the app generates 1-hour presigned download URLs. S3 lifecycle deletes objects after 24 hours. |

### Observability
- **CloudWatch Logs** — ECS task logs at `/ecs/pdf-tools`, 30-day retention.
- **ECS Container Insights** — cluster-level metrics.

## File Processing Flow

```
1. Browser uploads PDF(s) via POST /api/<tool>
2. FastAPI writes file(s) to a temporary directory under /tmp
   (via Python's tempfile.TemporaryDirectory context manager)
3. Tool script processes the file, writes output to the same temp directory
4. Result is uploaded to the temp S3 bucket
5. Python exits the TemporaryDirectory context — the entire temp directory
   and all its contents are deleted from the ECS task immediately
6. App returns a JSON response:
     { "download_url": "<1-hour presigned URL>", "filename": "..." }
7. Browser downloads the result directly from S3
8. S3 lifecycle deletes the object after 24 hours
```

Steps 5 and 6 happen in that order: the local files are gone before the response is even sent. The ECS task holds files in `/tmp` only for the duration of the processing step itself.

## Repository Structure

```
pdf_tools/
├── pdf_*.py                  CLI tool scripts (unchanged)
│
├── app/                      FastAPI web application
│   ├── main.py               App factory, CORS, error handler
│   ├── config.py             Settings from environment variables
│   ├── storage.py            S3 helpers (upload, presign, zip)
│   └── routers/              One file per tool group
│       ├── health.py         GET  /api/health
│       ├── merge.py          POST /api/merge
│       ├── split.py          POST /api/split/pages|ranges
│       ├── compress.py       POST /api/compress
│       ├── protect.py        POST /api/protect|decrypt
│       ├── rotate.py         POST /api/rotate
│       ├── reorder.py        POST /api/reorder
│       ├── ocr.py            POST /api/ocr
│       ├── watermark.py      POST /api/watermark
│       ├── page_numbers.py   POST /api/page-numbers
│       ├── convert.py        POST /api/to-images|to-docx|from-images
│       ├── redact.py         POST /api/redact/text|areas
│       ├── diff.py           POST /api/diff/report|visual
│       ├── inspect.py        POST /api/inspect
│       └── bookmarks.py      POST /api/bookmarks/list|add|remove
│
├── frontend/                 Static single-page application
│   ├── index.html
│   ├── style.css
│   └── app.js                All 22 tools defined as data; no build step
│
├── terraform/                Infrastructure as Code
│   ├── main.tf               Providers, backend config
│   ├── variables.tf
│   ├── outputs.tf
│   ├── vpc.tf                VPC, subnets, IGW, S3 gateway endpoint
│   ├── security_groups.tf    ALB SG, ECS SG
│   ├── s3.tf                 Frontend bucket + temp bucket
│   ├── acm.tf                TLS certificate (us-east-1)
│   ├── route53.tf            Subdomain hosted zone + A/AAAA records
│   ├── cloudfront.tf         Distribution, OAC, cache behaviours
│   ├── ecr.tf                Container registry
│   ├── alb.tf                Load balancer, listener, secret-header rule
│   ├── iam.tf                ECS execution role + task role
│   ├── ecs.tf                Cluster, task definition, service
│   └── github_actions.tf     OIDC provider, deploy role, Terraform role
│
└── .github/workflows/
    ├── tests.yml             PR: lint + unit tests
    ├── terraform.yml         PR: plan + comment; main: apply
    ├── deploy.yml            main: Docker→ECR→ECS + S3→CloudFront
    └── release.yml           main: version tag from Conventional Commits
```

## Cost Estimate (eu-west-1, low traffic)

| Resource | ~Monthly |
|---|---|
| ECS Fargate (0.5 vCPU, 2 GB, always-on) | $21 |
| ALB | $16 |
| Route53 hosted zone | $0.50 |
| CloudFront (free tier: 1 TB + 10M requests) | $0 |
| S3, ECR, CloudWatch | < $2 |
| **Total** | **~$40** |
