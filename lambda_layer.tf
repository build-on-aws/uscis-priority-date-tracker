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