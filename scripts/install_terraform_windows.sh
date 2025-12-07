#!/bin/bash
# Install Terraform on Windows (Git Bash)

set -e

echo "=========================================="
echo "Terraform Installation for Windows"
echo "=========================================="
echo ""

# Check if already installed
if command -v terraform >/dev/null 2>&1; then
    echo "✅ Terraform is already installed:"
    terraform --version
    exit 0
fi

echo "Terraform not found. Installing..."
echo ""

# Create terraform directory
TERRAFORM_DIR="/c/terraform"
mkdir -p "$TERRAFORM_DIR"

echo "Step 1: Downloading Terraform..."
echo ""

# Get latest Terraform version
TERRAFORM_VERSION=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' | sed 's/v//')

if [ -z "$TERRAFORM_VERSION" ]; then
    echo "Could not determine latest version, using 1.6.0"
    TERRAFORM_VERSION="1.6.0"
fi

echo "Latest version: $TERRAFORM_VERSION"
echo ""

# Download URL for Windows 64-bit
DOWNLOAD_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_windows_amd64.zip"
ZIP_FILE="/tmp/terraform.zip"

echo "Downloading from: $DOWNLOAD_URL"
echo ""

# Download using curl (Git Bash has curl)
curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"

if [ ! -f "$ZIP_FILE" ]; then
    echo "❌ Download failed"
    echo ""
    echo "Manual installation:"
    echo "1. Download from: https://releases.hashicorp.com/terraform/"
    echo "2. Extract terraform.exe to: $TERRAFORM_DIR"
    echo "3. Add to PATH: export PATH=\"$TERRAFORM_DIR:\$PATH\""
    exit 1
fi

echo "✅ Download complete"
echo ""

echo "Step 2: Extracting..."
cd "$TERRAFORM_DIR"
unzip -o "$ZIP_FILE" 2>/dev/null || {
    echo "unzip not found, trying alternative method..."
    # Try using PowerShell to extract
    powershell -Command "Expand-Archive -Path '$ZIP_FILE' -DestinationPath '$TERRAFORM_DIR' -Force" 2>/dev/null || {
        echo "❌ Extraction failed"
        echo "Please manually extract $ZIP_FILE to $TERRAFORM_DIR"
        exit 1
    }
}

echo "✅ Extraction complete"
echo ""

echo "Step 3: Adding to PATH..."
# Add to current session
export PATH="$TERRAFORM_DIR:$PATH"

# Add to .bashrc for persistence
BASHRC="$HOME/.bashrc"
if [ -f "$BASHRC" ]; then
    if ! grep -q "TERRAFORM_DIR" "$BASHRC"; then
        echo "" >> "$BASHRC"
        echo "# Terraform" >> "$BASHRC"
        echo "export PATH=\"/c/terraform:\$PATH\"" >> "$BASHRC"
        echo "✅ Added to ~/.bashrc"
    fi
else
    echo "export PATH=\"/c/terraform:\$PATH\"" > "$BASHRC"
    echo "✅ Created ~/.bashrc"
fi

echo ""

echo "Step 4: Verifying installation..."
if command -v terraform >/dev/null 2>&1; then
    terraform --version
    echo ""
    echo "✅ Terraform installed successfully!"
    echo ""
    echo "Note: If 'terraform --version' still fails, restart your terminal"
    echo "or run: source ~/.bashrc"
else
    echo "⚠️  Terraform not found in PATH"
    echo ""
    echo "Try:"
    echo "  export PATH=\"/c/terraform:\$PATH\""
    echo "  terraform --version"
    echo ""
    echo "Or restart your terminal"
fi

