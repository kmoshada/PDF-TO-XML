# PDF-TO-XML
Before running the code, checkto  install the,
  $ pip install PyMuPDF
  $ pip install flet
  $ pip install spacy
  $ python -m spacy download en_core_web_sm

Ao app
Run the app
uv
Run as a desktop app:

uv run flet run
Run as a web app:

uv run flet run --web
Poetry
Install dependencies from pyproject.toml:

poetry install
Run as a desktop app:

poetry run flet run
Run as a web app:

poetry run flet run --web
For more details on running the app, refer to the Getting Started Guide.

Build the app
Android
flet build apk -v
For more details on building and signing .apk or .aab, refer to the Android Packaging Guide.

iOS
flet build ipa -v
For more details on building and signing .ipa, refer to the iOS Packaging Guide.

macOS
flet build macos -v
For more details on building macOS package, refer to the macOS Packaging Guide.

Linux
flet build linux -v
For more details on building Linux package, refer to the Linux Packaging Guide.

Windows
flet build windows -v
For more details on building Windows package, refer to the Windows Packaging Guide.
