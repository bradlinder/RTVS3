# Google OAuth 2.0 Production Setup & Verification Guide

This guide is for the developer / maintainer of **Radio & TV Story Segmenter (RTVS)**. It provides end-to-end instructions for establishing, configuring, and verifying the production Google Cloud project and OAuth 2.0 Client ID so that end-users enjoy a seamless, "zero-config" experience.

---

## 1. Architectural Overview

Radio & TV Story Segmenter is a distributed desktop application (Windows & macOS). Under the official OAuth 2.0 specification for Native Apps ([RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252)) and Google's Desktop Application OAuth Profile:
1. **Public Client**: Desktop applications cannot keep a client secret confidential. Google Cloud Console generates a client secret for Desktop apps for historical OAuth 2.0 compatibility, but treats desktop clients as public clients.
2. **PKCE (Proof Key for Code Exchange, RFC 7636)**: RTVS generates a cryptographically random `code_verifier` and SHA-256 `code_challenge` (`S256`) on every login attempt. Google verifies this challenge upon token exchange, completely preventing authorization code interception.
3. **Local Loopback (`127.0.0.1`)**: RTVS binds a local loopback server to receive the authorization code. A unique, single-use 32-byte `state` token prevents CSRF and confused-deputy attacks.
4. **Least-Privilege Scopes**: RTVS requests only the scopes essential for document export and comment anchoring:
   - `https://www.googleapis.com/auth/documents` (Sensitive)
   - `https://www.googleapis.com/auth/drive.file` (Sensitive)
   - `https://www.googleapis.com/auth/userinfo.email` (Non-sensitive)

> **Important CASA Assessment Exemption**:
> Notice that RTVS uses `https://www.googleapis.com/auth/drive.file` rather than the broad `https://www.googleapis.com/auth/drive` scope. The `drive.file` scope grants access only to files created or opened by RTVS. Because RTVS does **not** request broad Restricted Google Drive scopes, it is **exempt from costly annual CASA Tier 2/3 third-party security audits**.

---

## 2. Google Cloud Console Setup

### Step 1: Create the Cloud Project
1. Log in to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top bar and click **New Project**.
3. Name the project `Radio and TV Story Segmenter` (or your organization name).
4. Click **Create**.

### Step 2: Enable Required APIs
1. Go to **APIs & Services > Library** (`https://console.cloud.google.com/apis/library`).
2. Search for and enable:
   - **Google Docs API** (`docs.googleapis.com`)
   - **Google Drive API** (`drive.googleapis.com`)

### Step 3: Configure the OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen** (`https://console.cloud.google.com/apis/credentials/consent`).
2. Select **External** user type and click **Create**.
3. **App Information**:
   - **App name**: `Radio & TV Story Segmenter`
   - **User support email**: Your public support or maintainer email.
   - **App logo**: Upload the official 120x120 PNG icon (matching the app icon).
4. **App Domain Information**:
   - **Application home page**: `https://github.com/bradlinder/RTVS3` (or your project website / documentation site).
   - **Application privacy policy link**: A public URL detailing your privacy policy (e.g. `https://github.com/bradlinder/RTVS3/blob/main/PRIVACY.md`).
     *Note: The privacy policy must explicitly state that user data, Google Docs, and tokens are stored locally on the user's machine and never transmitted to any third-party server.*
   - **Application terms of service link**: `https://github.com/bradlinder/RTVS3/blob/main/LICENSE` (or your terms page).
5. **Authorized Domains**:
   - Add your root domain (e.g., `github.com` or your personal domain if you host a docs site).
6. **Developer Contact Information**:
   - Enter your developer email address.
7. Click **Save and Continue**.

### Step 4: Configure Scopes
1. Click **Add or Remove Scopes**.
2. Select or enter:
   - `.../auth/userinfo.email` (Non-sensitive)
   - `.../auth/documents` (Sensitive)
   - `.../auth/drive.file` (Sensitive)
3. Do **NOT** select `.../auth/drive` (Restricted).
4. Click **Update** and then **Save and Continue**.

### Step 5: Create Desktop OAuth Client ID
1. Go to **APIs & Services > Credentials** (`https://console.cloud.google.com/apis/credentials`).
2. Click **+ Create Credentials > OAuth client ID**.
3. **Application type**: Select **Desktop app**.
4. **Name**: `Radio & TV Segmenter Desktop`.
5. Click **Create**.
6. Google will display your **Client ID** (e.g., `1049285718293-xxxxxxx.apps.googleusercontent.com`).
7. Copy this Client ID.

---

## 3. Embedding the Client ID in RTVS

1. Open `/plugins/gdocs/auth.py`.
2. Locate `DEFAULT_CLIENT_ID`:
   ```python
   DEFAULT_CLIENT_ID = "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"
   ```
3. Replace the placeholder with your production Client ID.
4. Save the file. Because desktop apps are public clients using PKCE, the client ID is distributed with the application. Users never need to enter credentials.

---

## 4. Google App Verification Process

When your OAuth consent screen is in "Testing" mode, only explicitly authorized test Google accounts can connect. To allow anyone to connect their Google account, you must submit the application for verification.

### Submission Requirements:
1. **Accurate App Branding**: App name, logo, support email, and homepage must match the application.
2. **Domain Ownership Verification**: Verify your support domain via Google Search Console.
3. **Privacy Policy**: Must clearly state:
   - What data RTVS accesses (creating Google Docs, placing them in selected Drive folders, attaching margin comments).
   - How data is stored (locally on user's device in native OS Keyring).
   - RTVS never shares, sells, or transmits data to any external server.
4. **Scope Justification**:
   - `https://www.googleapis.com/auth/documents`: Needed to format broadcast transcripts with bold speaker labels, timestamps, heading structures, and UTF-16 indexed styling requests via Docs API `documents.batchUpdate`.
   - `https://www.googleapis.com/auth/drive.file`: Needed to create new Google Docs, organize exports into designated project folders, and attach editorial margin comments.
   - `https://www.googleapis.com/auth/userinfo.email`: Needed to display the currently linked Google Account in the settings and export dialog.
5. **Demonstration Video**:
   Google requires a YouTube video link demonstrating the OAuth flow:
   - Show the user clicking "Connect Google Account" in RTVS.
   - Show the browser opening Google's consent screen.
   - Show the user granting permissions.
   - Show the browser displaying the success card and returning to RTVS.
   - Show RTVS creating a document and opening it in Google Docs.

Once submitted, Google typically reviews and approves Desktop apps using Sensitive scopes within 3–7 business days.
