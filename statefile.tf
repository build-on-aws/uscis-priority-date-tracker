terraform {
  backend "s3" {
    bucket         = "tf-us-visa-dates-checker"
    key            = "state.tfstate"
    region         = "us-west-2"
    dynamodb_table = "tf-us-visa-dates-checker-statelock"
    profile        = "development"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.53.0"
    }
  }

  required_version = ">= 1.8.5"
}