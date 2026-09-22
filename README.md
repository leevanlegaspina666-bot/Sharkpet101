 # Chibi Shark Pet — APK project

This project is already arranged for Android APK building.

## What it contains

- Kivy Android app
- All supplied PNG sprites in `assets/`
- Slow walking
- Random turns
- Walking animation
- Expressions and actions
- Physical jump
- Drag and release
- Tap does not freeze the pet
- YouTube sleepy behavior
- Messenger/Discord increased reactions
- No overlay over other apps

## Build without a computer

A GitHub Actions workflow is included at:

`.github/workflows/build-apk.yml`

You can use GitHub from an Android phone.

1. Create/sign in to a GitHub account.
2. Create a new repository.
3. Upload the files from this project, including the `.github` folder.
4. Open the repository's **Actions** tab.
5. Select **Build Chibi Shark Pet APK**.
6. Tap **Run workflow**.
7. Wait for the build to finish.
8. Open the completed workflow run.
9. Under **Artifacts**, download `chibi-shark-pet-apk`.
10. Extract the downloaded artifact and install the APK on Android.

GitHub builds the APK for you in the cloud, so no computer is required.

## Foreground-app detection

The app uses Android Usage Access to notice YouTube, Messenger, and Discord.

After installing the APK, if this feature doesn't work:

Android Settings → Apps / Special app access → Usage access → Chibi Shark Pet → Allow.

The exact menu wording varies by Android version.

## Important

This APK is an ordinary app window. It does NOT float over other apps.

YouTube/Messenger/Discord detection therefore affects the pet when the corresponding app is detected as foreground according to Android Usage Access; it does not put the pet on top of those apps.
