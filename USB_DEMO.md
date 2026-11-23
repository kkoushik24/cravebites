# 🍱 Dabba - USB Multi-Device Demo Guide

This guide explains how to run the **Dabba: Online Food Ordering System** in **one-click USB demo mode**:
- **Laptop Browser**: Restaurant Management Web Dashboard (`http://127.0.0.1:5002`)
- **Android Phone 1**: Customer Mobile App (`http://127.0.0.1:5001`)
- **Android Phone 2**: Delivery Partner Mobile App (`http://127.0.0.1:5003`)
- **Backend**: Python Flask REST API (`http://127.0.0.1:5000/api`)
- **Database**: Single MySQL 8 instance (`dabba_db`)

All communication uses **ADB Reverse Port Forwarding** over USB. No Wi-Fi or LAN IP configuration is required.

---

## 1. Prerequisites & Setup

### A. Android Platform-Tools (ADB)
Ensure `adb` is installed and accessible in your Windows system PATH:
1. Download Android SDK Platform-Tools for Windows: [developer.android.com/tools/releases/platform-tools](https://developer.android.com/tools/releases/platform-tools)
2. Extract the ZIP folder to `C:\platform-tools` (or check if already in `%LOCALAPPDATA%\Android\Sdk\platform-tools`).
3. Add the folder to your user/system `PATH` variable.
4. Verify by opening a command prompt and typing:
   ```cmd
   adb version
   ```

### B. Enable USB Debugging on Both Android Phones
On both Android devices:
1. Open **Settings** > **About phone**.
2. Tap **Build number** 7 times until you see the message *"You are now a developer!"*.
3. Go back to **Settings** > **System** (or **Additional settings**) > **Developer options**.
4. Enable **USB debugging**.
5. Connect both phones to your laptop via USB cables.
6. When prompted on each phone with *"Allow USB debugging?"*, check **Always allow from this computer** and tap **Allow**.

---

## 2. Launching the USB Demo

### Option 1: Double-Click the Batch File
Double-click `start_usb_demo.bat`.

### Option 2: Run via PowerShell
Open PowerShell in the project directory:
```powershell
.\start_usb_demo.ps1
```
*Tip: If you want to swap which phone runs which role, pass the `-Swap` flag:*
```powershell
.\start_usb_demo.ps1 -Swap
```

### What Happens Automatically:
1. Detects `adb` and verifies both connected Android devices.
2. Assigns **Phone 1** as the Customer App and **Phone 2** as the Delivery App.
3. Spawns 4 server terminal windows:
   - Port `5000`: Flask REST API Backend
   - Port `5001`: Customer PWA App
   - Port `5002`: Restaurant Management Web
   - Port `5003`: Delivery Partner PWA App
4. Health-checks `http://127.0.0.1:5000/api/health`.
5. Executes ADB reverse port forwards:
   - Phone 1: `reverse tcp:5000 tcp:5000` & `reverse tcp:5001 tcp:5001`
   - Phone 2: `reverse tcp:5000 tcp:5000` & `reverse tcp:5003 tcp:5003`
6. Opens the restaurant website in your laptop's default browser, and launches Chrome on both Android phones with their respective apps.

---

## 3. Stopping the Demo

When finished, run:
```cmd
stop_usb_demo.bat
```
This terminates all 4 web and backend processes and clears all ADB reverse port forwards (`adb reverse --remove-all`).

---

## 4. Live 5-Step Demo Script for Examiners & Evaluators

Follow these 5 steps to showcase the full end-to-end relational database flow:

### Step 1: Customer Places an Order (Phone 1)
- Tap **1-Click Demo Login** (or login with `customer@dabba.com` / `password123`).
- Browse dishes or use the 3D carousel / category filter (Biryani, Dosa, Thali, etc.).
- Add items from **Ember & Rice** (e.g. *Royal Awadhi Dum Biryani* + *Butter Garlic Naan*) to cart.
- Tap the floating cart bar, apply coupon `DABBA50`, select delivery address, and tap **Place Order**.
- Notice the live order tracking card appears with a 5-second polling interval and status **Placed**.

### Step 2: Restaurant Accepts the Order (Laptop Browser)
- On the laptop screen (`http://127.0.0.1:5002`), log in as `restaurant@dabba.com` / `password123`.
- The new order immediately appears in the **New** column with an alert pulse.
- Click **Accept**.
- The order card moves smoothly to the **Preparing** column.
- On Phone 1, the customer tracking card updates to **Preparing (Food is on the stove)**.

### Step 3: Kitchen Marks Order Ready (Laptop Browser)
- In the **Preparing** column on the laptop dashboard, click **Mark ready**.
- The order moves into the **Ready for pickup** column.
- The stored procedure triggers auto-assignment of the nearest available delivery partner with row locking (`FOR UPDATE`).

### Step 4: Delivery Partner Picks Up the Order (Phone 2)
- On Phone 2 (`http://127.0.0.1:5003`), log in as `delivery@dabba.com` / `password123`.
- The active dispatch card appears with the pickup location (*Ember & Rice*), drop location, payout (₹68), and 3D map route.
- Slide or drag the **Slide to confirm pickup** button to the right.
- The status updates to **Picked up**, and the slider label changes to **Slide to confirm delivery**.
- On Phone 1, customer tracking updates to **Rider on the way**.

### Step 5: Delivery Partner Delivers Order (Phone 2)
- Slide or drag the **Slide to confirm delivery** button to the right.
- Delivery completes! The delivery app transitions to the waiting radar view, and today's earnings/trips update.
- On the customer phone (Phone 1), the screen transitions to **Order Delivered** with a review card.
- Submit a 5-star rating and comment.
- Inspect the database table `audit_log` to observe every transition recorded by the database triggers:
  ```sql
  SELECT * FROM audit_log ORDER BY log_id DESC LIMIT 5;
  ```

---

## 5. Troubleshooting & FAQ

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **`device unauthorized`** | Phone hasn't approved RSA debugging key. | Unlock your phone screen, look for the USB debugging prompt, check "Always allow from this computer", and tap **Allow**. |
| **`Fewer than 2 devices found`** | USB cable loose or phone in "Charge only" mode. | Change USB mode to "File Transfer (MTP)" in notification shade. Check `adb devices`. |
| **Blank page on phone** | Reverse port forwarding was disconnected. | Re-run `start_usb_demo.bat`. Do not close the command prompt windows. |
| **Cable unplugged during demo** | Android OS drops ADB reverse ports when cable disconnects. | Reconnect the USB cable and run `start_usb_demo.bat` again. All open carts and login sessions will resume automatically. |
| **"Cannot reach the server" screen** | Backend is stopped or port forwarding lost. | Tap the **Retry Connection** button on screen. The apps auto-probe `/api/health` every 3 seconds and recover automatically once reconnected. |

