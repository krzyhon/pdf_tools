resource "random_password" "cf_secret" {
  length  = 32
  special = false
}

locals {
  s3_origin_id  = "S3-frontend"
  alb_origin_id = "ALB-api"

  cf_header_name  = "X-CF-Origin-Verify"
  cf_header_value = random_password.cf_secret.result
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.domain_name]
  price_class         = "PriceClass_100" # EU + North America only

  # ── Origins ────────────────────────────────────────────────────────────────

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = local.alb_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    # Secret header — ALB blocks any request that doesn't carry this
    custom_header {
      name  = local.cf_header_name
      value = local.cf_header_value
    }
  }

  # ── Cache behaviours ───────────────────────────────────────────────────────

  # Default: static frontend from S3 (cached)
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    compress = true
  }

  # /api/* → ALB (no caching, forward everything except Host header)
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = local.alb_origin_id
    viewer_protocol_policy = "redirect-to-https"

    # CachingDisabled managed policy
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"

    # AllViewerExceptHostHeader managed policy — forwards query strings,
    # headers, and cookies but replaces Host with the ALB hostname
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"

    compress = true
  }

  # ── TLS + restrictions ─────────────────────────────────────────────────────

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cloudfront.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Return index.html for unknown paths so the frontend can handle 404s
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }
}

# Expose the CloudFront secret to the ALB listener rule (defined in alb.tf)
output "cf_header_name" {
  value     = local.cf_header_name
  sensitive = false
}

output "cf_header_value" {
  value     = local.cf_header_value
  sensitive = true
}
