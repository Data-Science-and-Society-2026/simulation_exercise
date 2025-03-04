#requires -RunAsAdministrator
<#
.SYNOPSIS
   Checks if 'uv' is installed, and installs it if needed.
#>

[CmdletBinding()]
param()


Write-Host "Checking if 'uv' is installed..."
$uvInstalled = choco list --local-only | Select-String '^uv '
if ($null -ne $uvInstalled) {
    Write-Host "'uv' is already installed."
}
else {
    Write-Host "Installing 'uv' (Astral) via Chocolatey..."
    choco install uv -y
}
