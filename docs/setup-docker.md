# Setup Docker for the Translator stack

> **Sandbox limitation:** this workspace shell cannot install system
> packages. Run the steps below yourself on the host machine.

## Windows — Docker Desktop (recommended)

1. Enable WSL 2 (Admin PowerShell):
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```
   Reboot when prompted.

2. Download Docker Desktop:
   <https://www.docker.com/products/docker-desktop/>

3. Run the installer with **"Use WSL 2 backend"** ticked.

4. Open Docker Desktop once so it pulls the WSL distro and starts the
   engine. Verify:

   ```powershell
   docker info | Select-String "Server Version"
   docker compose version
   ```

5. From the repo root:
   ```powershell
   .\scripts\up.ps1 up     # or: docker compose -f infra/docker/docker-compose.yml up -d --build
   ```

6. Smoke test:
   ```powershell
   curl http://localhost:8000/healthz
   start http://localhost:3000
   start http://localhost:8233   # Temporal UI
   ```

## Linux — Docker Engine

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(. /etc/os-release; echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
docker info
```

## Podman (alternative)

```bash
sudo apt install -y podman podman-compose
podman-compose -f infra/docker/docker-compose.yml up -d --build
```

## Bare-metal quickstart (no Docker)

If you only need the Python packages locally:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api,worker,shared,dev]"
pip install temporalio
uvicorn translator_api.main:app --reload
```

The worker requires a Temporal server, which is the main reason we ship
the docker-compose dev environment.