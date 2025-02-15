#requires -RunAsAdministrator
<#
.SYNOPSIS
  Checks if Chocolatey is installed and installs it if missing.
  Then checks if 'uv' is installed, and installs it if needed.
#>

[CmdletBinding()]
param()

Write-Host "Checking if Chocolatey is installed..."
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey not found. Installing Chocolatey..."
    Write-Host "You may need to run this as Administrator for it to succeed."

    # Allow this process to run scripts
    Set-ExecutionPolicy Bypass -Scope Process -Force

    # Set TLS 1.2 (and beyond) to avoid download issues
    [System.Net.ServicePointManager]::SecurityProtocol = `
        [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

    # Download and run the official Chocolatey install script
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString(
        'https://community.chocolatey.org/install.ps1'
    ))

    Write-Host "Chocolatey installed."
}
else {
    Write-Host "Chocolatey is already installed."
}

Write-Host "Checking if 'uv' is installed..."
$uvInstalled = choco list --local-only | Select-String '^uv '
if ($null -ne $uvInstalled) {
    Write-Host "'uv' is already installed."
}
else {
    Write-Host "Installing 'uv' (Astral) via Chocolatey..."
    choco install uv -y
}
