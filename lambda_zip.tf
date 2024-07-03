# Zip of the application code
data "archive_file" "app" {
  type        = "zip"
  source_dir  = "${path.cwd}/src"
  output_path = "${path.cwd}/app.zip"
}
