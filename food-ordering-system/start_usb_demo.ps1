# ==============================================================================
# Dabba: Online Food Ordering System - Native Android USB Demo Launcher
# ==============================================================================
param (
    [switch]$Swap
)

# Optional manual device override (leave empty for auto-detection)
$CUSTOMER_SERIAL = ""
$DELIVERY_SERIAL = ""

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   🍱 DABBA - NATIVE ANDROID USB DEMO LAUNCHER          " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Resolve project root directories
$ROOT_DIR = $PSScriptRoot
if (-not (Test-Path "$ROOT_DIR\backend")) {
    if (Test-Path "$ROOT_DIR\food-ordering-system\backend") {
        $ROOT_DIR = "$ROOT_DIR\food-ordering-system"
    } else {
        Write-Host "[-] Error: Could not locate backend directory." -ForegroundColor Red
        exit 1
    }
}
$BACKEND_DIR = "$ROOT_DIR\backend"
$RESTAURANT_DIR = "$ROOT_DIR\restaurant-web"
$BUILDS_DIR = "$ROOT_DIR\builds"
if (-not (Test-Path "$BUILDS_DIR\dabba-customer.apk") -and (Test-Path "$PSScriptRoot\builds\dabba-customer.apk")) {
    $BUILDS_DIR = "$PSScriptRoot\builds"
}

$CUST_APK = "$BUILDS_DIR\dabba-customer.apk"
$RIDER_APK = "$BUILDS_DIR\dabba-rider.apk"

# 2. Verify APK builds exist
Write-Host "`n[*] Verifying APK build artifacts..." -ForegroundColor Cyan
if (-not (Test-Path $CUST_APK) -or -not (Test-Path $RIDER_APK)) {
    Write-Host "[-] Error: APK files not found in $BUILDS_DIR." -ForegroundColor Red
    Write-Host "    Please run .\build_apps.bat first to compile the Android apps." -ForegroundColor Yellow
    exit 1
}
Write-Host "[+] Found: $CUST_APK" -ForegroundColor Green
Write-Host "[+] Found: $RIDER_APK" -ForegroundColor Green

# 3. Check ADB availability
Write-Host "`n[*] Step 1: Checking ADB availability..." -ForegroundColor Cyan
$adbPath = (Get-Command adb -ErrorAction SilentlyContinue).Source
if (-not $adbPath) {
    $fallbackAdb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $fallbackAdb) {
        $env:PATH += ";$env:LOCALAPPDATA\Android\Sdk\platform-tools"
        $adbPath = $fallbackAdb
    }
}

if (-not $adbPath) {
    Write-Host "`n[-] ADB was NOT found in your PATH." -ForegroundColor Red
    Write-Host "To fix this:" -ForegroundColor Yellow
    Write-Host "  1. Download Android Platform Tools from:"
    Write-Host "     https://developer.android.com/tools/releases/platform-tools"
    Write-Host "  2. Extract the zip to a folder (e.g., C:\platform-tools)"
    Write-Host "  3. Add that folder to your Windows System PATH environment variable."
    Write-Host "  4. Restart your terminal and run this script again.`n"
    exit 1
}
Write-Host "[+] ADB detected: $adbPath" -ForegroundColor Green

# 4. Detect connected devices
Write-Host "`n[*] Step 2: Checking connected Android devices via 'adb devices'..." -ForegroundColor Cyan
$rawDevices = adb devices
$deviceList = @()
$unauthorizedFound = $false

foreach ($line in ($rawDevices -split "`r?`n")) {
    $trimmed = $line.Trim()
    if ($trimmed -and -not ($trimmed.StartsWith("List of devices"))) {
        $parts = -split $trimmed
        if ($parts.Length -ge 2) {
            $serial = $parts[0]
            $state = $parts[1]
            if ($state -eq "offline") {
                Write-Host "  [*] Device $serial is offline, attempting auto-reconnect..." -ForegroundColor Yellow
                adb -s $serial reconnect 2>&1 | Out-Null
                Start-Sleep -Seconds 1
                $state = "device"
            }
            if ($state -eq "device") {
                $deviceList += $serial
            } elseif ($state -eq "unauthorized") {
                $unauthorizedFound = $true
                Write-Host "  [!] Device $serial is UNAUTHORIZED." -ForegroundColor Yellow
            }
        }
    }
}

if ($unauthorizedFound) {
    Write-Host "`n[!] An unauthorized device was detected!" -ForegroundColor Yellow
    Write-Host "    Please check your phone screen and tap 'Always allow from this computer', then re-run." -ForegroundColor Yellow
}

Write-Host "Found $($deviceList.Count) authorized device(s):" -ForegroundColor Cyan
foreach ($d in $deviceList) {
    Write-Host "  - $d" -ForegroundColor White
}

# 5. Device assignment & role selection
if ($CUSTOMER_SERIAL -and $DELIVERY_SERIAL) {
    Write-Host "`n[*] Using manually configured serials:" -ForegroundColor Cyan
    $custPhone = $CUSTOMER_SERIAL
    $deliPhone = $DELIVERY_SERIAL
} else {
    if ($deviceList.Count -lt 2) {
        Write-Host "`n[-] USB Demo requires at least 2 connected Android devices with USB debugging enabled." -ForegroundColor Red
        Write-Host "    Only $($deviceList.Count) device(s) found." -ForegroundColor Red
        Write-Host "    Please connect both phones via USB and enable USB Debugging in Developer Options." -ForegroundColor Yellow
        exit 1
    }

    if ($Swap) {
        $custPhone = $deviceList[1]
        $deliPhone = $deviceList[0]
        Write-Host "`n[*] Role Swap Flag active (-Swap)." -ForegroundColor Magenta
    } else {
        $custPhone = $deviceList[0]
        $deliPhone = $deviceList[1]
    }
}

Write-Host "`n[+] Assigned Roles:" -ForegroundColor Green
Write-Host "  📱 Customer Phone: $custPhone (Installing 'Dabba')" -ForegroundColor White
Write-Host "  🛵 Delivery Phone: $deliPhone (Installing 'Dabba Rider')" -ForegroundColor White
Write-Host "  💻 Restaurant Web: Laptop Browser (http://127.0.0.1:5002)" -ForegroundColor White

# 6. Start servers in separate windows (Only Backend 5000 and Restaurant 5002)
Write-Host "`n[*] Step 3: Starting local servers on 127.0.0.1..." -ForegroundColor Cyan

# Start Backend (Port 5000)
Write-Host "  - Launching Flask Backend on port 5000..." -ForegroundColor White
Start-Process cmd.exe -ArgumentList "/k `"$BACKEND_DIR\run_backend.bat`""

# Start Restaurant Web (Port 5002)
Write-Host "  - Launching Restaurant Web on port 5002..." -ForegroundColor White
Start-Process cmd.exe -ArgumentList "/k `"$RESTAURANT_DIR\run_restaurant.bat`""

# 7. Wait for Backend Health Check
Write-Host "`n[*] Step 4: Waiting for backend health check at http://127.0.0.1:5000/api/health..." -ForegroundColor Cyan
$maxAttempts = 30
$healthy = $false
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($res.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 600
    }
}

if (-not $healthy) {
    Write-Host "[-] Backend failed to respond to /api/health within 18 seconds." -ForegroundColor Red
    Write-Host "    Please check the backend console window for database or startup errors." -ForegroundColor Yellow
    exit 1
}
Write-Host "[+] Backend is HEALTHY and listening on 127.0.0.1:5000" -ForegroundColor Green

# 8. Configure ADB reverse port forwarding on BOTH phones
Write-Host "`n[*] Step 5: Configuring ADB reverse port forwarding (tcp:5000 tcp:5000)..." -ForegroundColor Cyan
Write-Host "  - Forwarding port 5000 on Customer Phone ($custPhone)..." -ForegroundColor White
adb -s $custPhone reverse tcp:5000 tcp:5000
Write-Host "  - Forwarding port 5000 on Delivery Phone ($deliPhone)..." -ForegroundColor White
adb -s $deliPhone reverse tcp:5000 tcp:5000
Write-Host "[+] Port 5000 reverse forwarding active on both devices." -ForegroundColor Green

# 9. Install native Android APKs
Write-Host "`n[*] Step 6: Installing Native APKs onto assigned phones..." -ForegroundColor Cyan

Write-Host "  - Installing 'Dabba' (Customer) on Phone 1 ($custPhone)..." -ForegroundColor White
$custInstallOut = adb -s $custPhone install -r "$CUST_APK" 2>&1 | Out-String
if ($custInstallOut -match "Failure") {
    Write-Host "    [!] Retrying install with -d..." -ForegroundColor Yellow
    adb -s $custPhone install -r -d "$CUST_APK"
} else {
    Write-Host "    [+] Dabba installed successfully." -ForegroundColor Green
}

Write-Host "  - Installing 'Dabba Rider' (Delivery) on Phone 2 ($deliPhone)..." -ForegroundColor White
$riderInstallOut = adb -s $deliPhone install -r "$RIDER_APK" 2>&1 | Out-String
if ($riderInstallOut -match "Failure") {
    Write-Host "    [!] Direct install restricted: $($riderInstallOut.Trim())" -ForegroundColor Yellow
    if ($riderInstallOut -match "INSTALL_FAILED_USER_RESTRICTED") {
        Write-Host "    [!] Note: Phone 2 (Xiaomi/MIUI) requires 'Install via USB' in Developer options." -ForegroundColor Yellow
        Write-Host "    [*] Pushing APK to Phone 2 Downloads (/sdcard/Download/dabba-rider.apk)..." -ForegroundColor Cyan
        adb -s $deliPhone push "$RIDER_APK" /sdcard/Download/dabba-rider.apk 2>&1 | Out-Null
        Write-Host "    [*] Opening package installer on Phone 2 screen..." -ForegroundColor Cyan
        adb -s $deliPhone shell am start -a android.intent.action.VIEW -d "content://com.android.externalstorage.documents/document/primary:Download/dabba-rider.apk" -t "application/vnd.android.package-archive" 2>&1 | Out-Null
    } else {
        adb -s $deliPhone install -r -d "$RIDER_APK"
    }
} else {
    Write-Host "    [+] Dabba Rider installed successfully." -ForegroundColor Green
}
Write-Host "[+] APK installations finished." -ForegroundColor Green

# 10. Launch native apps (No browser!)
Write-Host "`n[*] Step 7: Launching native Android apps..." -ForegroundColor Cyan

Write-Host "  - Launching Dabba on Customer Phone ($custPhone)..." -ForegroundColor White
adb -s $custPhone shell am start -n com.dabba.customer/com.dabba.customer.MainActivity 2>&1 | Out-Null
adb -s $custPhone shell monkey -p com.dabba.customer -c android.intent.category.LAUNCHER 1 2>&1 | Out-Null

Write-Host "  - Launching Dabba Rider on Delivery Phone ($deliPhone)..." -ForegroundColor White
adb -s $deliPhone shell am start -n com.dabba.delivery/com.dabba.delivery.MainActivity 2>&1 | Out-Null
adb -s $deliPhone shell monkey -p com.dabba.delivery -c android.intent.category.LAUNCHER 1 2>&1 | Out-Null

# 11. Open Restaurant Web on laptop
Write-Host "`n[*] Step 8: Opening Restaurant Web on laptop..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:5002"

# 12. Summary and demo instructions
Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "          🎉 NATIVE ANDROID USB DEMO IS RUNNING!         " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Devices & Native Apps:" -ForegroundColor White
Write-Host "  📱 Phone 1 ($custPhone) : Native App 'Dabba' (com.dabba.customer)" -ForegroundColor White
Write-Host "  🛵 Phone 2 ($deliPhone) : Native App 'Dabba Rider' (com.dabba.delivery)" -ForegroundColor White
Write-Host "  💻 Laptop Browser       : Restaurant Dashboard (http://127.0.0.1:5002)" -ForegroundColor White
Write-Host ""
Write-Host "Demo Accounts (Password: password123 for all):" -ForegroundColor Yellow
Write-Host "  - Customer   : customer@dabba.com (Aarav Sharma)" -ForegroundColor White
Write-Host "  - Restaurant : restaurant@dabba.com (Ember & Rice)" -ForegroundColor White
Write-Host "  - Delivery   : delivery@dabba.com (Ravi Kumar)" -ForegroundColor White
Write-Host ""
Write-Host "Note:" -ForegroundColor Cyan
Write-Host "  - If a USB cable is unplugged, adb reverse will stop." -ForegroundColor White
Write-Host "    Simply reconnect the cable and run .\start_usb_demo.bat again to restore it." -ForegroundColor White
Write-Host "  - To stop all servers and clean up ADB port forwards, run .\stop_usb_demo.bat." -ForegroundColor White
Write-Host "==========================================================`n" -ForegroundColor Green
