# Define the Lambda function
resource "aws_lambda_function" "visa_bulletin_retriever" {
  function_name    = "visa-bulletin-retriever"
  handler          = "retriever.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.app.output_path
  source_code_hash = data.archive_file.app.output_base64sha256
  role             = aws_iam_role.retriever_role.arn
  layers           = [aws_lambda_layer_version.layer.arn]

  environment {
    variables = {
      BULLETIN_DATA           = aws_dynamodb_table.visa_bulletin_data.name,
      PROCESSED_BULLETIN_URLS = aws_dynamodb_table.processed_urls.name
    }
  }
}

# Define the IAM role for the Lambda function
resource "aws_iam_role" "retriever_role" {
  name = "visa-bulletin-retriever-role"

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
resource "aws_iam_role_policy_attachment" "retriever_lambda_basic_execution" {
  role       = aws_iam_role.retriever_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "retriever_dynamodb_access" {
  role       = aws_iam_role.retriever_role.name
  policy_arn = aws_iam_policy.retriever_dynamodb_access_policy.arn
}

# Define the IAM policy for DynamoDB access
resource "aws_iam_policy" "retriever_dynamodb_access_policy" {
  name   = "visa-bulletin-retriever-dynamodb-access"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
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