# Scanflow updates

Official Scanflow Android APK releases by Bhupinder Singh.

**[Download the latest Scanflow APK](https://github.com/bhupindermotushydraulics-sketch/scanflow-updates/releases/latest/download/Scanflow.apk)**

## One-time setup on each device

1. Install the latest APK over your existing Scanflow installation. Keep the existing app installed so its records and settings remain available.
2. Open **Settings → App updates → Allow app updates**, then enable **Allow from this source** for Scanflow.
3. Leave **Automatic updates** enabled. Allow update notifications so Android can ask for confirmation if necessary.

The app checks approximately every 15 minutes when Android permits background work. Downloads use Wi-Fi by default. Installation waits until Scanflow is in the background, so it does not deliberately interrupt active scanning. Reopen Scanflow after an update.

Android controls installation permissions. Some devices allow unattended self-updates; others require a confirmation tap. Battery saving, force-stop, network restrictions and older Android versions can delay updates. GitHub cannot override these controls.

## Publishing future updates

Build and sign the `fleet` APK with the existing Scanflow preview signing key. Keep the same application ID (`app.scanflow.mobile.preview`), increase `versionCode`, and give the release the matching version tag (for example `v1.3.1`).

Create a GitHub release, attach the signed APK named **Scanflow.apk**, and publish it. The workflow automatically verifies the package, signing certificate and version, calculates its checksum, and publishes the update feed. Devices then discover it automatically. Check that **Publish verified Scanflow update** succeeds in Actions.

The repository contains release automation and APKs only. **Do not upload the private source ZIP, keystores, signing backup, passwords, Google credentials or scan records here.** App development and building a new signed release remain necessary; this workflow automates distribution after publishing.

## Privacy

Update checks and downloads connect to GitHub, which receives ordinary network information such as the IP address. Scanflow does not send barcodes, sheet content, Google credentials or session details to GitHub. Automatic updates can be disabled in Settings.

Support: bhupindermotushydraulics@gmail.com
