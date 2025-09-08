#!/bin/bash

# Exit on any command failure
set -e

# Log all output for debugging
exec > >(tee -i setup.log) 2>&1

echo "Starting setup at $(date)"

# Install Azure CLI
echo "Installing Azure CLI..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl apt-transport-https lsb-release gnupg
curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | sudo tee /usr/share/keyrings/microsoft-prod.gpg > /dev/null
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
sudo apt-get update
sudo apt-get install -y azure-cli

# Log in to Azure with a Service Principal
echo "Logging in to Azure..."
export AZURE_CLIENT_ID="AAAAAAAAAAAAAAAAAAA7"
export AZURE_CLIENT_SECRET="AAAAAAAAAAAAAAAAAAAAAAAAA"
export AZURE_TENANT_ID="36AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA032"
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

# Generate SSH key pair in the current directory
echo "Generating SSH key pair..."
ssh-keygen -t rsa -b 4096 -f ./id_rsa -N ""

# Install dependencies
echo "Installing dependencies..."
sudo apt-get install -y wget unzip netcat-traditional || sudo apt-get install -y netcat-openbsd

# Verify netcat installation
if ! command -v nc >/dev/null 2>&1; then
  echo "Error: netcat not installed. Trying to install netcat-openbsd..."
  sudo apt-get install -y netcat-openbsd
  if ! command -v nc >/dev/null 2>&1; then
    echo "Warning: netcat not found. Using curl as fallback for SSH check."
  fi
fi

# Install Terraform
echo "Installing Terraform..."
TERRAFORM_VERSION="1.13.0"
wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip
sudo mv terraform /usr/local/bin/
rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Install Ansible
echo "Installing Ansible..."
sudo apt-get install -y ansible

# Verify installations
terraform --version
az --version
ansible --version

# Disable Terraform colored output to prevent ANSI characters
export TF_CLI_ARGS="-no-color"

# Check for and remove stale Terraform state lock
if [ -f terraform.tfstate ]; then
  echo "Checking for stale Terraform state lock..."
  terraform force-unlock -force fa536576-0fb5-68a0-b6cb-51fa98ae51b9 || echo "No lock to remove or lock ID changed"
fi

# Run Terraform
echo "Initializing Terraform..."
terraform init

echo "Planning Terraform deployment..."
terraform plan -out=tfplan

echo "Applying Terraform configuration..."
terraform apply -auto-approve tfplan

# Extract the public IP of the created VM
echo "Retrieving VM private IP..."
VM_PRIVATE_IP=$(terraform output -no-color -raw private_ip_address)

# Create Ansible inventory file
echo "Creating Ansible inventory file..."
cat > inventory.yml << EOL
---
all:
  hosts:
    microedge-vm:
      ansible_host: ${VM_PRIVATE_IP}
      ansible_user: azureuser
      ansible_ssh_private_key_file: ./id_rsa
      ansible_ssh_common_args: '-o StrictHostKeyChecking=no'
EOL

# Wait for VM to be ready (SSH port available)
echo "Waiting for VM to be ready..."
if command -v nc >/dev/null 2>&1; then
  timeout 300 bash -c "until nc -zv $VM_PRIVATE_IP 22; do sleep 5; done"
else
  echo "Using curl as fallback for SSH check..."
  timeout 300 bash -c "until curl --connect-timeout 5 -s telnet://$VM_PRIVATE_IP:22; do sleep 5; done"
fi

# Run Ansible playbook
echo "Running Ansible playbook to configure Edge Microgateway..."
ansible-playbook -i inventory.yml microedge_ansible_installation.yml

echo "Setup completed successfully at $(date). Microgateway VM is deployed and configured."
