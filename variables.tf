variable "aws_profile" {
    default = "development"
}

variable "aws_region" {
  default = "us-west-2"
}

variable "state_file_bucket_name" {
  default = "tf-us-visa-dates-checker"
}

variable "state_file_lock_table_name" {
  default = "tf-us-visa-dates-checker-statelock"
}

variable "kms_key_alias" {
  default = "tf-us-visa-dates-checker"
}