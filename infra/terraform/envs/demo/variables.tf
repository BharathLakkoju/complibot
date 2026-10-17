variable "aws_region" {
  type        = string
  description = "AWS region for the single-EC2 demo stack."
  default     = "ap-south-1"
}

variable "project" {
  type        = string
  description = "Project tag value."
  default     = "complibot"
}

variable "environment" {
  type        = string
  description = "Environment name."
  default     = "demo"
}

variable "instance_type" {
  type        = string
  description = "ARM Graviton instance; t4g.micro fits the <$10/mo demo budget with ~20 GB gp3."
  default     = "t4g.micro"
}

variable "root_volume_gb" {
  type        = number
  description = "Root EBS gp3 size (GB) for Docker images + Postgres data."
  default     = 20
}

variable "ssh_cidr" {
  type        = string
  description = "CIDR allowed to SSH (port 22). Restrict to your IP before apply."

  validation {
    condition     = var.ssh_cidr != "0.0.0.0/0"
    error_message = "ssh_cidr must not be 0.0.0.0/0; set your office or home IP (e.g. 203.0.113.10/32)."
  }
}

variable "api_cidr" {
  type        = string
  description = "CIDR allowed to reach HTTPS (443) and HTTP (80 for ACME)."
  default     = "0.0.0.0/0"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "Vercel (or other) origins allowed for S3 presigned PUT CORS."
  default     = ["https://your-vercel-app.vercel.app"]
}

variable "ssh_key_name" {
  type        = string
  description = "Optional EC2 key pair name in the target region for SSH."
  default     = ""
}

variable "repository_url" {
  type        = string
  description = "Git clone URL baked into user-data (deploy script still does git pull)."
  default     = "https://github.com/BharathLakkoju/complibot.git"
}

variable "api_domain" {
  type        = string
  description = "Public DNS name for the API (Caddy + Let's Encrypt on the EC2 host)."
}

variable "acme_email" {
  type        = string
  description = "Email for Let's Encrypt expiry notices (used by Caddy on the host)."
}
