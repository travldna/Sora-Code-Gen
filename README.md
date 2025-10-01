# Sora Code Gen

> **⚠️ Important Notice: Use at Your Own Risk**
>
> This script is provided for **educational purposes only**. Automating requests to a website's API may violate the Terms of Service of Sora/OpenAI. Using this script could potentially result in your account being suspended or banned. You are solely responsible for how you use this tool. The author of this script assumes no liability. Proceed with caution.

---

### Recommended Setup

For the best results, it is highly recommended to use the **Mozilla Firefox** browser and connect to a **VPN server located in the USA**. This helps to match the request headers that are most commonly accepted by the API.

---

## How It Works

1.  **Generates Codes**: The script creates random 6-character invite codes in the format `0A1B2C`.
2.  **Submits Codes**: It uses multiple threads to submit these codes to the Sora API as fast as possible.
3.  **Handles Responses**:
    *   If a code is **successful** (200 OK), it's saved to `success.txt`.
    *   If a code is **invalid** (403 Forbidden), it's saved to `invalid_codes.txt` and never tried again.
    *   If the script is **rate-limited** (429 Too Many Requests), it waits and retries.
    *   If your **authentication fails** (401 Unauthorized), the script will stop and tell you to update your token.
4.  **Smart Blacklist & Cache**: The script is intelligent. It uses `used_codes.txt` and `invalid_codes.txt` as a "blacklist cache". Every time it starts, it loads these files to ensure it **never tries the same code twice**, whether it was successful, invalid, or simply attempted before. This makes the script highly efficient, especially when you stop and restart it.

---

## Setup Guide

Follow these steps carefully to get the script running.

### Step 1: Initial Installation

1.  Make sure you have [Python](https://www.python.org/downloads/) installed.
2.  Double-click the `install.bat` file. It will automatically create a virtual environment and install the necessary library.

### Step 2: Get Your Authentication Token (Firefox)

This is the most important step. The script needs your personal authentication token to work.

1.  Open **Mozilla Firefox** and log in to `https://sora.chatgpt.com`.
2.  Press the `F12` key to open the **Developer Tools**.
3.  Go to the **Network** tab.
4.  If the list is empty, refresh the page or navigate to `https://sora.chatgpt.com/explore`.
5.  In the filter box (🔍), type `sora` to show only requests to the Sora server.
6.  Click on any request in the list.
7.  On the right, find the **Headers** section and scroll down to **Request Headers**.
8.  Look for the `authorization` header. It will look like this:
    `authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...`
9.  **Copy the long string of characters** *after* the word `Bearer `.
10. Paste the token you copied into `auth.txt`. **Do not include `Bearer `**. Save the file.

### Step 3: Customize Script Parameters (Optional)

You can fine-tune the script's performance by editing the `params.txt` file.

-   `max_workers`: The number of threads used to submit codes. More threads can be faster but may increase the chance of being rate-limited.
-   `delay`: The pause (in seconds) between processing codes. A higher delay is safer.
-   `max_retries`: How many times the script will try to resubmit a code if it gets a rate-limit error.
-   `retry_delay`: The base time (in seconds) the script waits before retrying.

If you are unsure, the default values in `params.txt` are a good starting point.

### Step 4: Get Your Device ID and User Agent (Firefox)

The script needs to look like it's coming from your specific browser.

1.  In the same **Network** tab where you found your token, look for the `OAI-Device-Id` and `User-Agent` headers, usually below the auth token.
2.  Copy the values for both.
3.  Open the `config.txt` file that came with the script.
4.  Replace the placeholder values with your own `OAI-Device-Id` and `User-Agent`. Save the file.

### Step 5: Run the Script

Once you have completed the steps above, you are ready to run the script.

**On Windows:**
-   Double-click the `run.bat` file.

The script will start running and show you its progress. Press `Ctrl+C` to stop it at any time.

---

## File Descriptions

-   `sora.py`: The main Python script.
-   `auth.txt`: **(You edit this)** Your secret authentication token.
-   `config.txt`: **(You edit this)** Your browser's Device ID and User Agent.
-   `params.txt`: **(You edit this)** Script parameters like thread count and delays.
-   `install.bat`: **(Run this first)** Sets up the Python virtual environment.
-   `run.bat`: **(Run this to start)** Activates the environment and starts the script.
-   `success.txt`: Automatically created. Contains all successfully submitted codes.
-   `used_codes.txt`: Automatically created. Contains all codes the script has tried.
-   `invalid_codes.txt`: Automatically created. A "blacklist" of codes that are known to be invalid.
