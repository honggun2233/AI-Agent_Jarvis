# Jarvis Windows Task Scheduler Setup
# 관리자 권한 PowerShell에서 실행: .\scripts\setup-scheduler.ps1

$JarvisDir = "C:\Users\Samsung\Jarvis"
$PythonPath = (Get-Command python).Source

Write-Host "Jarvis 작업 스케줄러 등록 중..." -ForegroundColor Cyan

# 1. 매일 오전 8시 모닝 브리핑
$action1 = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "$JarvisDir\skills\morning-briefing\scripts\morning_briefing.py" `
    -WorkingDirectory $JarvisDir

$trigger1 = New-ScheduledTaskTrigger -Daily -At "08:00AM"

$settings1 = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "Jarvis-MorningBriefing" `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -RunLevel Highest `
    -Force

Write-Host "✅ Jarvis-MorningBriefing 등록 완료 (매일 08:00)" -ForegroundColor Green

# 2. 로그인 시 OpenClaw 자동 시작
$OpenClawPath = (Get-Command openclaw -ErrorAction SilentlyContinue)?.Source
if (-not $OpenClawPath) {
    $OpenClawPath = "$env:APPDATA\npm\openclaw.cmd"
}

$action2 = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c openclaw start" `
    -WorkingDirectory $JarvisDir

$trigger2 = New-ScheduledTaskTrigger -AtLogOn

$settings2 = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

Register-ScheduledTask `
    -TaskName "Jarvis-OpenClaw" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -RunLevel Highest `
    -Force

Write-Host "✅ Jarvis-OpenClaw 등록 완료 (로그인 시 자동 시작)" -ForegroundColor Green

Write-Host ""
Write-Host "등록된 작업 확인:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName "Jarvis-*" | Select-Object TaskName, State
