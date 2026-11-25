# StudentLedger LR3 - create one Ubuntu 24.04 VM for TEST/STAGE/PROD.
# ASCII only: Windows PowerShell 5.1 may read .ps1 as ANSI.
#
# Example:
#   & scripts/lr03/create-vm.ps1 -Name studentledger-test -Hostname studentledger-test `
#       -Iso "$env:USERPROFILE\Downloads\ubuntu-24.04.5-live-server-amd64.iso" `
#       -SshPort 2221 -Mac 08002751a001

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Name,
  [Parameter(Mandatory = $true)][string]$Hostname,
  [Parameter(Mandatory = $true)][string]$Iso,
  [Parameter(Mandatory = $true)][int]$SshPort,
  [Parameter(Mandatory = $true)][string]$Mac,
  [string]$User = 'student',
  [string]$Password = 'StudentLedger2026!',
  [int]$MemoryMb = 3072,
  [int]$Cpus = 2,
  [int]$DiskMb = 20480,
  [string]$VBoxManage = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',
  [string]$HostOnlyAdapter = 'VirtualBox Host-Only Ethernet Adapter'
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Iso)) { throw "ISO not found: $Iso" }

$vmDir = Join-Path $env:USERPROFILE "VirtualBox VMs\$Name"
$disk = Join-Path $vmDir "$Name.vdi"

& $VBoxManage createvm --name $Name --ostype Ubuntu24_LTS_64 --register --basefolder (Join-Path $env:USERPROFILE 'VirtualBox VMs')
& $VBoxManage modifyvm $Name --memory $MemoryMb --cpus $Cpus --vram 64 --graphicscontroller vmsvga --audio none
& $VBoxManage modifyvm $Name --nic1 nat --nic2 hostonly --hostonlyadapter2 $HostOnlyAdapter --macaddress2 $Mac
& $VBoxManage modifyvm $Name --natpf1 "ssh,tcp,127.0.0.1,$SshPort,,22"
& $VBoxManage modifyvm $Name --ioapic on --rtcuseutc on

& $VBoxManage createmedium disk --filename $disk --size $DiskMb --format VDI
& $VBoxManage storagectl $Name --name SATA --add sata --controller IntelAhci --portcount 2
& $VBoxManage storageattach $Name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk

& $VBoxManage unattended install $Name `
    --iso=$Iso `
    --user=$User `
    --user-password=$Password `
    --full-user-name='Student' `
    --hostname=$Hostname `
    --locale=en_US `
    --country=RU `
    --time-zone=Europe/Moscow `
    --start-vm=headless

Write-Host "VM $Name is installing. SSH will be available on 127.0.0.1:$SshPort."
