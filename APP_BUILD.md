# 📱 Dabba - Android Native Apps & USB Demo Guide

This guide details how to build and run the **native Android APKs** for **Dabba** (Customer App) and **Dabba Rider** (Delivery App) and execute the one-click USB multi-device demo:
- **Phone 1**: Native App `Dabba` (`com.dabba.customer`, `dabba-customer.apk`)
- **Phone 2**: Native App `Dabba Rider` (`com.dabba.delivery`, `dabba-rider.apk`)
- **Laptop**: Restaurant Management Web Dashboard (`http://127.0.0.1:5002`) & Backend API (`http://127.0.0.1:5000/api`)

Web assets are compiled directly inside the APK packages. Communication runs strictly through **ADB Reverse Port Forwarding** over USB. No phone browsers or Wi-Fi networks are used.

---

## 1. Required Software & Prerequisites

| Software | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Node.js & npm** | Node 20+ / 22+ (LTS) | Package management and Capacitor CLI (`npx cap sync`) |
| **Java Development Kit (JDK)** | JDK 17 or 21 (LTS) | Required by Android Gradle Plugin (AGP) and Gradle 8.11 |
| **Android SDK & Platform Tools** | API 34+ (`build-tools 34.0.0+`) | Compiles native Android code and provides `adb.exe` |
| **Android Studio** | Optional (recommended) | Bundles Android SDK, emulator, and build tools |

Ensure `adb` is in your Windows system PATH:
```cmd
adb version
```
Set environment variables if not automatically detected:
- `JAVA_HOME`: e.g. `C:\Users\<username>\.jdks\ms-21.0.13.0.2` or `C:\Program Files\Java\jdk-21`
- `ANDROID_HOME`: e.g. `%LOCALAPPDATA%\Android\Sdk`

---

## 2. Enabling USB Debugging on Both Phones

1. Open **Settings** > **About phone** on each Android phone.
2. Tap **Build number** 7 times until you see the message *"You are now a developer!"*.
3. Go to **Settings** > **Developer options**.
4. Turn on **USB debugging**.
5. Connect both phones to your laptop with USB data cables.
6. When the popup *"Allow USB debugging?"* appears, check **Always allow from this computer** and tap **Allow**.
7. Confirm with:
   ```cmd
   adb devices
   ```
   Both devices must display state `device` (not `unauthorized` or `offline`).

---

## 3. How to Build the APKs

Run the automated build script:
```cmd
build_apps.bat
```

### What `build_apps.bat` does automatically:
1. Validates Node.js, JDK (17/21), and the Android SDK.
2. Syncs web assets into the Capacitor Android container (`npx cap sync android`).
3. Runs the Gradle build (`gradlew.bat assembleDebug`) for:
   - `customer-app` -> `builds/dabba-customer.apk` (Package: `com.dabba.customer`, Name: *"Dabba"*)
   - `delivery-app` -> `builds/dabba-rider.apk` (Package: `com.dabba.delivery`, Name: *"Dabba Rider"*)
4. Outputs the finished installable APKs directly into the `builds/` directory.

---

## 4. Running the One-Click USB Demo

### Step 1: Double-Click the Launcher
Run:
```cmd
start_usb_demo.bat
```
*(Or in PowerShell: `.\start_usb_demo.ps1`)*

*Tip: If you want to swap which phone runs which app, run:*
```powershell
.\start_usb_demo.ps1 -Swap
```

### What Happens Automatically:
1. Detects both connected phones via `adb devices`.
2. Assigns Phone 1 as Customer and Phone 2 as Delivery.
3. Starts the Flask backend (port 5000) and Restaurant Web (port 5002) in titled command windows.
4. Waits for `http://127.0.0.1:5000/api/health` to respond.
5. Configures ADB reverse port forwarding on both devices (`adb reverse tcp:5000 tcp:5000`).
6. Installs `dabba-customer.apk` onto Phone 1 and `dabba-rider.apk` onto Phone 2 (`adb install -r`).
7. Natively launches each app via Android system intent (No browser used).
8. Opens the Restaurant Dashboard on your laptop browser.

---

## 5. Stopping the Demo

To stop all servers and remove all reverse port forwarding tunnels:
```cmd
stop_usb_demo.bat
```

---

## 6. Live 5-Step Demo Script for Evaluators

### Step 1: Customer Places an Order (Native App on Phone 1)
- Tap the **Dabba** app on Phone 1.
- Tap **⚡ 1-Click Demo Login** (`customer@dabba.com`).
- Browse menu items from *Ember & Rice* (e.g. *Royal Awadhi Dum Biryani* + *Butter Garlic Naan*).
- Tap the floating cart bar, apply promo code `DABBA50`, select delivery address, and tap **Place Order**.
- Real-time status card appears showing **Placed**.

### Step 2: Kitchen Accepts Order (Laptop Browser)
- In the laptop browser (`http://127.0.0.1:5002`), log in as `restaurant@dabba.com` / `password123`.
- The new order arrives in the **New** Kanban column with a visual glow.
- Click **Accept**.
- The card moves to **Preparing**, and Phone 1 live-updates to **Food is on the stove** within 5 seconds.

### Step 3: Kitchen Marks Order Ready (Laptop Browser)
- On the laptop dashboard in the **Preparing** column, click **Mark ready**.
- Order moves to the **Ready for pickup** column.
- The MySQL stored procedure executes a row-locked transaction (`FOR UPDATE`) and assigns delivery partner Ravi Kumar.

### Step 4: Delivery Partner Picks Up (Native App on Phone 2)
- Open the **Dabba Rider** app on Phone 2.
- Tap **⚡ 1-Click Demo Login** (`delivery@dabba.com`).
- The active dispatch card appears with restaurant pickup address, drop address, earnings (₹68), and 3D map route.
- Drag or slide the **Slide to confirm pickup** control to the right.
- Status updates to **Picked up**, and the slider label changes to **Slide to confirm delivery**.
- Phone 1 live-updates to **Rider on the way**.

### Step 5: Delivery Partner Completes Delivery (Native App on Phone 2)
- Slide the **Slide to confirm delivery** control.
- Delivery completes! The delivery app transitions back to the waiting radar view, and today's earnings/trips update.
- Phone 1 displays **Order Delivered** with a 5-star review sheet.
- Submit a 5-star rating to trigger an update in the MySQL `audit_log` table.

---

## 7. Troubleshooting & FAQ

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **`device unauthorized`** | RSA key not yet approved on the phone screen. | Unlock phone, check "Always allow from this computer", and tap **Allow**. |
| **`INSTALL_FAILED_UPDATE_INCOMPATIBLE`** | App installed previously with a different debug signature. | Uninstall the previous version from phone settings or run `adb -s <serial> uninstall <package>` and re-run. |
| **`INSTALL_FAILED_USER_RESTRICTED`** | Xiaomi/MIUI/Oppo/Realme requires "Install via USB" permission. | Go to Developer Options, enable **Install via USB** (and **USB debugging (Security settings)** if prompted). |
| **App opens but shows "Cannot reach server"** | ADB reverse port forward was lost. | Tap the **Retry Connection** button. The app auto-probes `/api/health` every 3s. If cable was unplugged, reconnect and run `start_usb_demo.bat`. |
| **Cable unplugged during presentation** | Android drops ADB reverse on cable disconnect. | Reconnect the USB cable and run `start_usb_demo.bat`. The apps will resume automatically without losing session state. |
| **Gradle build error / Java version mismatch** | Wrong JDK version set in environment. | Ensure `JAVA_HOME` points to JDK 17 or 21 (e.g., `C:\Users\<user>\.jdks\ms-21.0.13.0.2`), not Java 8 or Java 25. |

