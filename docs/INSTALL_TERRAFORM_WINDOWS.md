# Installing Terraform on Windows

Quick guide to install Terraform on Windows (Git Bash).

## Option 1: Automated Script (Recommended)

```bash
./scripts/install_terraform_windows.sh
```

This script will:
1. Download latest Terraform
2. Extract to `C:\terraform`
3. Add to PATH
4. Verify installation

## Option 2: Manual Installation

### Step 1: Download Terraform

1. Go to: https://releases.hashicorp.com/terraform/
2. Download latest Windows 64-bit version (e.g., `terraform_1.6.0_windows_amd64.zip`)
3. Extract `terraform.exe` to a folder (e.g., `C:\terraform`)

### Step 2: Add to PATH

**Option A: Add to Git Bash PATH (Session Only)**
```bash
export PATH="/c/terraform:$PATH"
terraform --version
```

**Option B: Add to Git Bash PATH (Permanent)**
```bash
# Add to ~/.bashrc
echo 'export PATH="/c/terraform:$PATH"' >> ~/.bashrc
source ~/.bashrc
terraform --version
```

**Option C: Add to Windows PATH (System-Wide)**

1. Right-click "This PC" → Properties
2. Advanced System Settings → Environment Variables
3. System Variables → Path → Edit
4. Add: `C:\terraform`
5. OK → OK
6. Restart Git Bash

### Step 3: Verify

```bash
terraform --version
# Should show: Terraform v1.x.x
```

## Option 3: Using Chocolatey

If you have Chocolatey installed:

```powershell
# Run PowerShell as Administrator
choco install terraform
```

Then restart Git Bash.

## Option 4: Using Scoop

If you have Scoop installed:

```bash
scoop install terraform
```

## Troubleshooting

### "terraform: command not found" after adding to PATH

1. **Restart Git Bash** - PATH changes require restart
2. **Check path exists:**
   ```bash
   ls /c/terraform/terraform.exe
   ```
3. **Verify PATH:**
   ```bash
   echo $PATH
   # Should include /c/terraform
   ```
4. **Try full path:**
   ```bash
   /c/terraform/terraform.exe --version
   ```

### Download fails

Manual download:
1. Visit: https://releases.hashicorp.com/terraform/
2. Download Windows 64-bit ZIP
3. Extract `terraform.exe` to `C:\terraform`
4. Add to PATH as above

### Permission denied

If you get permission errors:
- Run Git Bash as Administrator
- Or install to a user directory: `C:\Users\YourName\terraform`

## Verify Installation

After installation:

```bash
terraform --version
terraform -help
```

You should see Terraform version and help text.

## Next Steps

Once Terraform is installed:

```bash
# Verify all prerequisites
./scripts/deploy_to_eks.sh ap-southeast-2
```

Or follow the manual deployment guide: [DEPLOY_EKS_STEP_BY_STEP.md](DEPLOY_EKS_STEP_BY_STEP.md)

