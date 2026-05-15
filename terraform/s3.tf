resource "random_id" "suffix" {
  byte_length = 4
}

# ── Frontend bucket (private, served via CloudFront OAC) ──────────────────────

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Bucket policy: only CloudFront can read objects
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  # CloudFront distribution must exist before this policy can reference its ARN
  depends_on = [aws_cloudfront_distribution.main]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.main.arn
        }
      }
    }]
  })
}

# ── Temp files bucket (private, pre-signed URLs, auto-expired) ────────────────

resource "aws_s3_bucket" "temp_files" {
  bucket = "${var.project_name}-temp-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "temp_files" {
  bucket                  = aws_s3_bucket.temp_files.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Objects expire after 1 day as a safety net; pre-signed download URLs are
# generated with a 1-hour TTL so users can't access files after that window.
resource "aws_s3_bucket_lifecycle_configuration" "temp_files" {
  bucket = aws_s3_bucket.temp_files.id

  rule {
    id     = "expire-temp-files"
    status = "Enabled"

    expiration {
      days = 1
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "temp_files" {
  bucket = aws_s3_bucket.temp_files.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT"]
    allowed_origins = ["https://${var.domain_name}"]
    max_age_seconds = 3600
  }
}
