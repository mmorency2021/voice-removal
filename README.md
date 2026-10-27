# MP3 Vocal Remover

A local web tool for creating backing tracks from audio files. Choose **Lead vocal** to reduce the main singer while trying to keep backing vocals, or **All vocals** to reduce singing generally.

**The default is to run directly with Python and FFmpeg. No Docker or Podman is required.** Containers are optional deployment alternatives only.

Audio is processed on the machine running the app. It is not uploaded to a separation service. The app downloads open-source software and model files when required, then caches the models for reuse.

## Features

- MP3, WAV, FLAC, M4A and OGG input, up to 500 MB per file.
- Two separation modes with independently cached models.
- Processing status, browser playback and a 320 kbps MP3 download.
- One processing job at a time to limit CPU and memory usage.
- A local browser interface with no account or API key required.
- Mac, Windows and Linux launchers; Docker or Podman are optional.

Separation is approximate: overlapping voices, reverb and the original mix can leave vocal remnants or reduce backing vocals or instruments. "Lead vocal" aims to preserve backing vocals; it cannot guarantee doing so.

## Run on this Mac (default, no container)

This copy already has a private Python environment and cached models in this folder.

1. Double-click **Launch.command**, or run:

   ```bash
   cd /Users/mmorency/mp3-removal
   ./run.sh
   ```

2. Keep the Terminal window open. The browser opens automatically.
3. Choose a song, select a mode and click **Create backing track**.
4. Listen to the result and click **Download MP3**.
5. Press **Control-C** in Terminal to stop the server after processing finishes.

Each launch chooses a free local port. For a fixed address instead:

```bash
./run.sh --port 7860
```

Open <http://127.0.0.1:7860>.

## Install from a fresh GitHub clone (no container)

### Requirements

- Python 3.11 or 3.12 (recommended).
- FFmpeg available on `PATH`.
- A C compiler for dependencies built from source (Xcode Command Line Tools on macOS; `build-essential` and Python headers on Debian/Ubuntu).
- Internet access for the initial package/model downloads.
- Enough free memory and disk space for PyTorch, models and temporary audio. Processing speed depends on the CPU and track length.

### macOS

Install [Homebrew](https://brew.sh/) if needed. Open Terminal and install the prerequisites:

```bash
brew install python@3.12 ffmpeg
```

If a dependency needs a compiler, install Apple's Command Line Tools with `xcode-select --install` and finish its installer before continuing.

Download the repository using GitHub's **Code > Download ZIP** and extract it, or clone it with Git:

```bash
git clone https://github.com/YOUR-OWNER/mp3-removal.git
cd mp3-removal
./run.sh
```

Replace `YOUR-OWNER` with the actual GitHub account or organization. The launcher creates `.venv`, installs `requirements.txt` and opens the browser. The first use of each mode downloads its model.

If you downloaded the ZIP, open Terminal in the extracted folder and run `bash run.sh`, or double-click `Launch.command` if macOS permits it. Keep the Terminal window open while using the tool. On later uses, launch it the same way; packages and models are reused.

### Windows 10 / 11 (64-bit, no container)

1. Install **64-bit Python 3.12** from [Python's Windows downloads](https://www.python.org/downloads/windows/). Include the Python launcher (`py`) when offered. Python 3.11 also works; avoid choosing a newer Python release for this setup.
2. Install FFmpeg from a Windows build linked on the [official FFmpeg downloads page](https://ffmpeg.org/download.html). Extract it to a location such as `C:\ffmpeg`, then add the directory containing `ffmpeg.exe` (for example `C:\ffmpeg\bin`) to your user **Path** environment variable. Close and reopen terminals after changing Path.
3. Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), selecting **Desktop development with C++**, the MSVC compiler and a Windows SDK. Some audio dependencies need to compile during setup. Restart if the installer requests it.
4. On GitHub, use **Code > Download ZIP**, extract the entire project to a folder such as `C:\Tools\mp3-removal`, then double-click **run.cmd**. A Git installation is not needed for the ZIP method.
5. Wait for the first-time dependency installation. The browser opens automatically. Choose a song, choose a mode and click **Create backing track**. Each mode downloads its model when first used.

You can also run these commands in **Command Prompt** from the extracted folder:

```bat
py -3.12 --version
ffmpeg -version
run.cmd
```

For a fixed port:

```bat
run.cmd --port 7860
```

Then open <http://127.0.0.1:7860>. Keep the Command Prompt window open; press **Ctrl+C** to stop after processing finishes. No administrator account is needed to launch the app after prerequisites are installed.

If you prefer manual setup:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

GitHub Actions is configured to run the included HTTP tests on Windows and Linux once the repository is pushed. Actual Windows audio installation/inference still needs verification on a Windows machine; Mac and Linux-container checks do not prove that path works.

### Moving to another computer

Copy or download the **source files**, then run that computer's launcher. Do not copy `.venv` between Macs, Windows and Linux; Python environments are specific to the operating system and architecture. The new computer creates its own `.venv` and downloads models. No container is needed.

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-dev build-essential ffmpeg libsndfile1 git
git clone https://github.com/YOUR-OWNER/mp3-removal.git
cd mp3-removal
./run.sh --port 7860 --no-browser
```

Use a distribution with Python 3.11 or 3.12, or install one of those versions separately. Open <http://127.0.0.1:7860> on that machine.

To install manually instead of using the launcher:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py --port 7860
```

## Optional: deploy with Docker

Docker Engine/Desktop with Docker Compose is required.

```bash
git clone https://github.com/YOUR-OWNER/mp3-removal.git
cd mp3-removal
docker compose up --build -d
docker compose logs -f
```

Open <http://127.0.0.1:7860>. This deployment publishes the port only on the host's loopback interface. The app binds to all interfaces **inside the container** so Docker can reach it.

Named volumes keep downloaded models and results between container replacements:

- `audio-models`: downloaded separation models.
- `audio-data`: job outputs, temporary files and caches.

Stop the deployment without deleting those volumes:

```bash
docker compose down
```

After updating the code:

```bash
git pull
docker compose up --build -d
```

## Optional: deploy with Podman instead of Docker

Podman uses the same `Dockerfile`; Docker and a Compose provider are not required for these commands.

### Install and prepare Podman

On macOS, install Podman using the [official installer](https://podman.io/docs/installation). Create a Linux VM once, then start it:

```bash
podman machine init
podman machine start
```

If you already have a Podman machine, skip `init`. If it is already running, skip `start`. On Linux, Podman runs directly without a VM. For example:

```bash
# Ubuntu / Debian
sudo apt-get install -y podman

# Fedora / RHEL with Podman available in the configured repositories
sudo dnf install -y podman
```

### Build and run

From the repository directory:

```bash
podman build -t localhost/mp3-removal:latest .
podman volume create mp3-removal-data
podman volume create mp3-removal-models
podman run -d --name mp3-removal \
  -p 127.0.0.1:7860:7860 \
  -v mp3-removal-data:/app/data:U \
  -v mp3-removal-models:/app/models:U \
  localhost/mp3-removal:latest
podman logs -f mp3-removal
```

Open <http://127.0.0.1:7860>. The two named volumes retain job files and cached models. The `:U` option sets ownership of these dedicated volumes for the non-root user inside the image; see the [Podman volume documentation](https://docs.podman.io/en/latest/markdown/podman-run.1.html).

Stop and restart the existing container:

```bash
podman stop mp3-removal
podman start mp3-removal
```

To replace the container after a code update:

```bash
git pull
podman build -t localhost/mp3-removal:latest .
podman stop mp3-removal
podman rm mp3-removal
```

Then repeat the `podman run` command above. Removing the container does not remove these separately named volumes. The Podman port mapping, like the Docker configuration, exposes the app only on the host's loopback address.

## Access a deployment on a remote Linux server

Keep the provided loopback-only port mapping for either Docker or Podman, start the deployment on the server, then forward the port from your own computer:

```bash
ssh -N -L 7860:127.0.0.1:7860 USER@SERVER
```

Open <http://127.0.0.1:7860> in your local browser while the SSH connection remains open. Audio uploads travel to your own server through that connection.

The included app is designed for local/private use. It has no user accounts or public-service authentication; public hosting would require an authenticated gateway and appropriate request/resource limits. The supplied deployment keeps it private.

## Storage and configuration

By default, everything generated stays under the project directory:

```text
mp3-removal/
  app.py              Local HTTP server
  worker.py           Audio separation and MP3 export
  index.html          Browser interface
  run.sh              macOS/Linux launcher and first-time setup
  Launch.command      Double-click launcher for macOS
  run.cmd             Windows launcher and first-time setup
  requirements.txt    Python dependencies
  Dockerfile
  compose.yaml
  tests/              Fast HTTP smoke tests
  models/             Downloaded weights (ignored by Git)
  data/
    jobs/JOB-ID/
      result.mp3      Completed backing track
      processing.log  Diagnostic log
```

Optional environment variables:

- `VOCAL_REMOVER_DATA_DIR`: absolute path for job files and caches.
- `VOCAL_REMOVER_MODELS_DIR`: absolute path for downloaded models.

The worker deletes temporary input and WAV files after a successful export. Failed jobs retain their files and log for troubleshooting. Results remain on disk until you delete them; stop the app before clearing job folders. Browser job state is held in memory by the server, so after a server restart, retrieve older results directly from `data/jobs/`.

## Development and checks

The HTTP tests use only the Python standard library and do not download models:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile app.py worker.py
bash -n run.sh
```

GitHub Actions runs these checks on pushes and pull requests. To test actual separation, start the app and process a short audio sample in each mode. Model inference is intentionally excluded from CI to avoid large downloads and long jobs.

## Push to GitHub

The local project is initialized on the `main` branch. Create an empty repository named `mp3-removal` on GitHub, then use its actual remote URL:

```bash
git remote add origin https://github.com/YOUR-OWNER/mp3-removal.git
git push -u origin main
```

If there is no initial commit yet:

```bash
git add .
git commit -m "Add local MP3 vocal removal tool"
```

`.gitignore` excludes songs, generated audio, model weights, logs, caches, `.env` files and `.venv`. Fresh clones download their own dependencies and models. Do not use `git add -f` to bypass those exclusions for private files.

## Troubleshooting

- **FFmpeg missing:** install it using the OS commands above and relaunch.
- **Compiler missing during installation:** install `build-essential` and `python3-dev` on Debian/Ubuntu, Xcode Command Line Tools on macOS (`xcode-select --install`), or Microsoft C++ Build Tools with the Desktop development with C++ workload on Windows, then retry.
- **Windows cannot find `py` or `ffmpeg`:** finish installing the prerequisites and open a new Command Prompt. Check `py -3.12 --version` and `ffmpeg -version` before rerunning `run.cmd`.
- **Model download fails:** check internet access and retry. Models are cached under `models/`.
- **Processing fails:** inspect the job's `processing.log` file under `data/jobs/`.
- **High memory usage:** process one shorter file at a time. The app already limits processing to one active job.
- **Browser cannot connect:** keep Terminal/the container running and use the URL printed at startup. Check `docker compose logs` or `podman logs mp3-removal` for a container deployment.
- **Vocal bleed or lost harmonies:** try the other mode and compare the result. There is no universally perfect separation setting.

## Credits

Built using [Audio Separator](https://github.com/nomadkaraoke/python-audio-separator), the [Ultimate Vocal Remover model collection](https://github.com/TRvlvr/model_repo), [PyTorch](https://pytorch.org/) and [FFmpeg](https://ffmpeg.org/).

Lead-vocal mode uses `UVR_MDXNET_KARA_2.onnx`; all-vocals mode uses `UVR-MDX-NET-Inst_HQ_3.onnx`. Third-party software and models retain their respective licenses and terms.
