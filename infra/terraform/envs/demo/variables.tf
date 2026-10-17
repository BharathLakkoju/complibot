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
  description = "CIDR allowed to reach the API (port 8000) and HTTP (port 80 for optional reverse proxy)."
  default     = "0.0.0.0/0"
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
