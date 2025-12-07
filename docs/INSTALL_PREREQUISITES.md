# Installing Prerequisites for EKS Deployment

This guide helps you install all required tools for deploying SearchOp to AWS EKS.

## Required Tools

- AWS CLI
- Terraform (>= 1.0)
- kubectl
- Docker
- Python 3.11+

## Windows Installation

### 1. AWS CLI

**Option A: Using MSI Installer (Recommended)**
1. Download: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run installer
3. Verify: `aws --version`

**Option B: Using pip**
```bash
pip install awscli
```

### 2. Terraform

**Option A: Using Chocolatey (Recommended)**
```bash
# Install Chocolatey first if needed: https://chocolatey.org/install
choco install terraform
```

**Option B: Manual Installation**
1. Download: https://releases.hashicorp.com/terraform/
2. Choose Windows 64-bit version
3. Extract `terraform.exe` to a folder in your PATH (e.g., `C:\Program Files\Terraform`)
4. Add to PATH:
   - Right-click "This PC" → Properties → Advanced System Settings
   - Environment Variables → System Variables → Path → Edit
   - Add: `C:\Program Files\Terraform`
5. Verify: `terraform --version`

**Option C: Using Scoop**
```bash
scoop install terraform
```

### 3. kubectl

**Option A: Using Chocolatey**
```bash
choco install kubernetes-cli
```

**Option B: Using curl (Git Bash)**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/windows/amd64/kubectl.exe"
mv kubectl.exe /usr/local/bin/kubectl
chmod +x /usr/local/bin/kubectl
```

**Option C: Using Scoop**
```bash
scoop install kubectl
```

### 4. Docker

1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify: `docker --version`

### 5. Python 3.11+

You already have Python 3.13.0 installed ✅

## Verify All Tools

Run this to check everything is installed:

```bash
echo "Checking prerequisites..."
aws --version
terraform --version
kubectl version --client
docker --version
python --version
```

## Configure AWS

After installing AWS CLI:

```bash
aws configure
```

Enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `ap-southeast-2` (or your preferred region)
- **Default output format**: `json`

Verify:
```bash
aws sts get-caller-identity
```

## Troubleshooting

### Terraform not found in Git Bash

If Terraform is installed but not found in Git Bash:

1. Find where Terraform is installed:
   ```bash
   where terraform  # Windows CMD
   # or
   which terraform  # Git Bash (if in PATH)
   ```

2. Add to Git Bash PATH:
   - Edit `~/.bashrc` or `~/.bash_profile`
   - Add: `export PATH="/c/Program Files/Terraform:$PATH"`
   - Or add to Windows PATH and restart Git Bash

### Docker not running

Make sure Docker Desktop is running:
- Check system tray for Docker icon
- Start Docker Desktop if not running

### AWS CLI not working

If `aws` command not found:
- Restart terminal after installation
- Check PATH includes AWS CLI location
- Try: `C:\Program Files\Amazon\AWSCLIV2\aws.exe --version`

## Quick Install Script (PowerShell)

If you have Chocolatey installed:

```powershell
# Run PowerShell as Administrator
choco install awscli terraform kubernetes-cli docker-desktop -y
```

Then restart your terminal.

## Next Steps

Once all tools are installed:

```bash
# Verify
./scripts/deploy_to_eks.sh ap-southeast-2
```

Or follow the manual steps in [DEPLOY_EKS_STEP_BY_STEP.md](DEPLOY_EKS_STEP_BY_STEP.md)

