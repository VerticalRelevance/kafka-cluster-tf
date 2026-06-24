terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
  bucket = "kafka-tf-state-899456967600"
  key    = "terraform.tfstate"
  region = "us-east-2"
}
}

provider "aws" {
  region = "us-east-2"
}