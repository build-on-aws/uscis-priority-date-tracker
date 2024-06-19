resource "aws_dynamodb_table" "visa_bulletin_data" {
  name           = "VisaBulletinData"
  billing_mode   = "PAY_PER_REQUEST"

  hash_key       = "pk"
  range_key      = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }
}

resource "aws_dynamodb_table" "processed_urls" {
  name           = "ProcessedURLs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "url"

  attribute {
    name = "url"
    type = "S"
  }
}

# Install dependencies and create the Lambda layer package
resource "null_resource" "pip_install" {
  triggers = {
    shell_hash = "${sha256(file("${path.cwd}/src/requirements.txt"))}"
  }

  provisioner "local-exec" {
    command = <<EOF
        cd src
        echo "Create and activate venv"
        python3 -m venv package
        source package/bin/activate
        mkdir -p ${path.cwd}/layer/python
        echo "Install dependencies to ${path.cwd}/layer/python"
        pip3 install -r requirements.txt -t ${path.cwd}/layer/python
        deactivate
        cd ..
    EOF
  }
}

# Zip up the app to deploy as a layer
data "archive_file" "layer" {
  type        = "zip"
  source_dir  = "${path.cwd}/layer"
  output_path = "${path.cwd}/layer.zip"
  depends_on  = [null_resource.pip_install]
}

# Create the Lambda layer with the dependencies
resource "aws_lambda_layer_version" "layer" {
  layer_name          = "dependencies-layer"
  filename            = data.archive_file.layer.output_path
  source_code_hash    = data.archive_file.layer.output_base64sha256
  compatible_runtimes = ["python3.12", "python3.11"]
}

# Zip of the application code
data "archive_file" "app" {
  type        = "zip"
  source_dir  = "${path.cwd}/src"
  output_path = "${path.cwd}/app.zip"
}

# Define the Lambda function
resource "aws_lambda_function" "visa_bulletin_scraper" {
  function_name    = "visa-bulletin-scraper"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.app.output_path
  source_code_hash = data.archive_file.app.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  layers           = [aws_lambda_layer_version.layer.arn]

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.visa_bulletin_data.name
    }
  }
}

# Define the IAM role for the Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "visa-bulletin-scraper-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

# Attach the necessary IAM policies to the role
resource "aws_iam_policy_attachment" "lambda_basic_execution" {
    name = "lambda_basic_execution"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_policy_attachment" "dynamodb_access" {
    name = "dynamodb_access"
  policy_arn = aws_iam_policy.dynamodb_access_policy.arn
  roles      = [aws_iam_role.lambda_role.name]
}

# Define the IAM policy for DynamoDB access
resource "aws_iam_policy" "dynamodb_access_policy" {
  name = "visa-bulletin-scraper-dynamodb-access"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "${aws_dynamodb_table.processed_urls.arn}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "${aws_dynamodb_table.visa_bulletin_data.arn}"
    }
  ]
}
EOF
}