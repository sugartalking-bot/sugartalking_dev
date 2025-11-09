# Sugartalking Kubernetes Installer
# Windows PowerShell installation script
#
# Usage: .\installer.ps1 [-Namespace <name>] [-ImageRegistry <registry>] [-ImageTag <tag>]
#

param(
    [string]$Namespace = "default",
    [string]$ImageRegistry = "ghcr.io/builderoftheworlds",
    [string]$ImageTag = "latest",
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
Sugartalking Kubernetes Installer for Windows

Usage: .\installer.ps1 [options]

Options:
  -Namespace <name>       Kubernetes namespace (default: default)
  -ImageRegistry <url>    Container registry (default: ghcr.io/builderoftheworlds)
  -ImageTag <tag>         Image tag (default: latest)
  -Help                   Show this help message

Examples:
  .\installer.ps1
  .\installer.ps1 -Namespace sugartalking
  .\installer.ps1 -ImageTag v2.0.0
"@
    exit 0
}

# Color functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check kubectl
    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Write-Error "kubectl not found. Please install kubectl first."
        Write-Info "Download from: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
        exit 1
    }

    # Check cluster connection
    try {
        kubectl cluster-info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw
        }
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    }

    Write-Success "Prerequisites check passed"
}

# Create namespace
function New-NamespaceIfNeeded {
    Write-Info "Checking namespace '$Namespace'..."

    kubectl get namespace $Namespace 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Info "Namespace '$Namespace' already exists"
    }
    elseif ($Namespace -ne "default") {
        Write-Info "Creating namespace '$Namespace'..."
        kubectl create namespace $Namespace
        Write-Success "Namespace created"
    }
}

# Setup GitHub secret
function New-GitHubSecret {
    Write-Info "Setting up GitHub token for error reporting..."

    kubectl get secret sugartalking-secrets -n $Namespace 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Info "GitHub secret already exists"
        return
    }

    $response = Read-Host "Do you want to configure GitHub error reporting? (y/N)"
    if ($response -match "^[Yy]$") {
        $secureToken = Read-Host "Enter GitHub personal access token" -AsSecureString
        $token = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
        )

        if ($token) {
            kubectl create secret generic sugartalking-secrets `
                --from-literal=GITHUB_TOKEN="$token" `
                -n $Namespace
            Write-Success "GitHub secret created"
        }
        else {
            Write-Warning "No token provided, skipping secret creation"
        }
    }
    else {
        Write-Info "Skipping GitHub secret setup"
    }
}

# Apply manifests
function Install-Manifests {
    Write-Info "Applying Kubernetes manifests..."

    # Change to base directory
    Push-Location base

    try {
        # Update namespace in manifests if not default
        if ($Namespace -ne "default") {
            Write-Info "Updating namespace in manifests to '$Namespace'..."
            Get-ChildItem -Filter "*.yaml" | ForEach-Object {
                (Get-Content $_.FullName) -replace 'namespace: default', "namespace: $Namespace" |
                    Set-Content $_.FullName
            }
        }

        # Apply in order
        kubectl apply -f persistentvolumeclaim.yaml
        kubectl apply -f configmap.yaml
        kubectl apply -f deployment.yaml
        kubectl apply -f service.yaml

        # Ask about ingress
        $response = Read-Host "Do you want to install Ingress? (requires ingress controller) (y/N)"
        if ($response -match "^[Yy]$") {
            kubectl apply -f ingress.yaml
            Write-Success "Ingress created"
        }

        Write-Success "Manifests applied"
    }
    finally {
        Pop-Location
    }
}

# Wait for deployment
function Wait-ForDeployment {
    Write-Info "Waiting for deployment to be ready..."

    kubectl wait --for=condition=available --timeout=300s `
        deployment/sugartalking -n $Namespace

    Write-Success "Deployment is ready!"
}

# Display access information
function Show-AccessInfo {
    Write-Info "Fetching access information..."
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  Sugartalking Installation Complete! 🎉" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""

    # Get pod name
    $podName = kubectl get pods -n $Namespace -l app=sugartalking -o jsonpath='{.items[0].metadata.name}'
    Write-Host "Pod Name: $podName"
    Write-Host ""

    # Check for ingress
    kubectl get ingress sugartalking -n $Namespace 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $hostname = kubectl get ingress sugartalking -n $Namespace -o jsonpath='{.spec.rules[0].host}'
        Write-Host "Access URL: http://$hostname"
        Write-Host ""
        Write-Info "Make sure '$hostname' is in your hosts file (C:\Windows\System32\drivers\etc\hosts)"
    }
    else {
        Write-Host "To access Sugartalking, use port-forward:"
        Write-Host "  kubectl port-forward -n $Namespace svc/sugartalking 5000:80"
        Write-Host ""
        Write-Host "Then visit: http://localhost:5000"
    }

    Write-Host ""
    Write-Host "Admin Panel: http://localhost:5000/admin"
    Write-Host ""
    Write-Host "View logs:"
    Write-Host "  kubectl logs -n $Namespace -l app=sugartalking -f"
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
}

# Cleanup on error
function Remove-OnError {
    Write-Error "Installation failed. Rolling back..."
    kubectl delete -f base/ -n $Namespace --ignore-not-found=true 2>&1 | Out-Null
    exit 1
}

# Main installation
function Start-Installation {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Sugartalking Kubernetes Installer   ║" -ForegroundColor Cyan
    Write-Host "║        Universal AVR Control          ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Change to script directory
    Set-Location $PSScriptRoot

    try {
        Test-Prerequisites
        New-NamespaceIfNeeded
        New-GitHubSecret
        Install-Manifests
        Wait-ForDeployment
        Show-AccessInfo

        Write-Success "Installation completed successfully!"
    }
    catch {
        Remove-OnError
    }
}

# Run installation
Start-Installation
