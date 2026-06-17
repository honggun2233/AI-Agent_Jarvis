# Jarvis Scripts

## setup-scheduler.ps1

Windows 작업 스케줄러에 Jarvis 자동 실행 작업을 등록합니다.

### 실행 방법

관리자 권한 PowerShell에서:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup-scheduler.ps1
```

### 등록되는 작업

| 작업명 | 실행 시점 | 내용 |
|--------|-----------|------|
| Jarvis-MorningBriefing | 매일 08:00 | 모닝 브리핑 Telegram 전송 |
| Jarvis-OpenClaw | 로그인 시 | OpenClaw 게이트웨이 자동 시작 |

### 작업 확인

```powershell
Get-ScheduledTask -TaskName "Jarvis-*"
```

### 작업 삭제 (필요 시)

```powershell
Unregister-ScheduledTask -TaskName "Jarvis-MorningBriefing" -Confirm:$false
Unregister-ScheduledTask -TaskName "Jarvis-OpenClaw" -Confirm:$false
```
