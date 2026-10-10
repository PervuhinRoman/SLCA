# StudentLedger LR2 - provision a VirtualBox VM from the Windows host.
#
# Purpose: deliver helper scripts into the guest, enable passwordless
# administration and run the in-guest provisioning (minimal GUI, LR2 tools,
# static address, project clone, systemd service).
#
# Why this file exists: in VirtualBox 7.2 `VBoxManage guestcontrol run` has no
# stdin support, and `copyto` fails against this guest additions build. Files are
# therefore transferred in base64 chunks passed as command arguments.
#
# NOTE: this script is intentionally ASCII-only. Windows PowerShell 5.1 reads
# .ps1 files as ANSI unless they carry a UTF-8 BOM, which corrupts non-ASCII
# text and breaks parsing. Keep it ASCII.
#
# Usage (from the repository root):
#   & scripts/lr02/provision-vm.ps1 -Vm studentledger-stage `
#       -VmHostname studentledger-stage `
#       -Netplan scripts/lr02/netplan-192.168.56.12-stage.yaml

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Vm,
  [Parameter(Mandatory = $true)][string]$VmHostname,
  [Parameter(Mandatory = $true)][string]$Netplan,
  [string]$VBoxManage = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',
  [string]$User = 'student',
  [string]$Password = 'StudentLedger2026!',
  [string]$RepoUrl = 'https://github.com/PervuhinRoman/SLCA.git'
)

$ErrorActionPreference = 'Stop'
$chunkSize = 900

function Invoke-Guest {
  param([string]$Program, [string[]]$Arguments)
  & $VBoxManage guestcontrol $Vm run --username=$User --password=$Password --exe $Program -- @Arguments
}

function Send-GuestFile {
  param([string]$HostPath, [string]$GuestPath)
  if (-not (Test-Path $HostPath)) { throw "missing host file: $HostPath" }
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($HostPath))
  Invoke-Guest -Program /bin/rm -Arguments @('-f', '/tmp/part.000.b64') | Out-Null
  $n = 0
  for ($i = 0; $i -lt $b64.Length; $i += $chunkSize) {
    $len = [Math]::Min($chunkSize, $b64.Length - $i)
    $n++
    $tmp = '/tmp/part.{0:d3}.b64' -f $n
    Invoke-Guest -Program /bin/sh -Arguments @('-c', "printf '%s' '$($b64.Substring($i, $len))' > $tmp") | Out-Null
  }
  $join = 'cat /tmp/part.*.b64 | base64 -d > ' + $GuestPath + '; chmod 644 ' + $GuestPath + '; rm -f /tmp/part.*.b64; wc -c < ' + $GuestPath
  $r = Invoke-Guest -Program /bin/sh -Arguments @('-c', $join)
  $size = ($r | Out-String).Trim()
  $hostSize = (Get-Item $HostPath).Length
  if ($size -ne "$hostSize") { throw "size mismatch for $GuestPath : guest=$size host=$hostSize" }
  Write-Host "  delivered $GuestPath ($size bytes, chunks: $n)"
}

function Enable-PasswordlessSudo {
  $lines = @(
    "printf '%s\n' '$User ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-student-ledger",
    'chmod 440 /etc/sudoers.d/90-student-ledger',
    'visudo -c'
  ) -join "`n"
  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($lines))
  Invoke-Guest -Program /bin/sh -Arguments @('-c', "printf '%s\n' '$Password' > /home/$User/.sudo-pass; chmod 600 /home/$User/.sudo-pass") | Out-Null
  $cmd = "echo $b64 | base64 -d > /tmp/payload.sh; sudo -S -p '' bash /tmp/payload.sh < /home/$User/.sudo-pass 2>&1"
  Invoke-Guest -Program /bin/bash -Arguments @('-c', $cmd) | Out-String | Write-Host
  $id = (Invoke-Guest -Program /usr/bin/sudo -Arguments @('-n', '/usr/bin/id') | Out-String).Trim()
  if ($id -notmatch 'uid=0') { throw "administrator rights not available: $id" }
  Write-Host "  administrator rights confirmed: $id"
}

Write-Host "== $Vm : delivering scripts =="
Send-GuestFile -HostPath (Join-Path $PSScriptRoot 'provision-vm.sh') -GuestPath "/home/$User/provision-vm.sh"
Send-GuestFile -HostPath (Resolve-Path $Netplan).Path -GuestPath "/home/$User/netplan-internal.yaml"

Write-Host "== $Vm : administrator rights =="
Enable-PasswordlessSudo

Write-Host "== $Vm : provisioning (GUI, tools, network, project) =="
$env:REPO_URL = $RepoUrl
& $VBoxManage guestcontrol $Vm run --username=$User --password=$Password --timeout=3600000 `
    --exe /usr/bin/sudo -- -n /bin/bash "/home/$User/provision-vm.sh" $VmHostname "/home/$User/netplan-internal.yaml"
Write-Host "== $Vm : finished, exit code $LASTEXITCODE =="
