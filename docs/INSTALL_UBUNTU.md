# Installing OpenUBA on Ubuntu Server

This guide covers running OpenUBA on a headless **Ubuntu 22.04 / 24.04 Server**.
The [main install guide](INSTALL.md) targets a macOS development laptop; this
one documents the Linux-server specifics — remote access, the ports Kind binds,
and the handful of issues you can hit on a fresh box.

> Originally contributed by the community in
> [issue #116](https://github.com/GACWR/OpenUBA/issues/116) (thanks to
> **@rock0ne**) and folded into the repo as the official Linux path.

There are two ways to install: the **automated script** (recommended) or the
**manual steps** if you'd rather understand each one.

---

## Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| OS      | Ubuntu 22.04 / 24.04 LTS Server | Desktop works too |
| RAM     | 8 GB   | 16 GB recommended (Kind runs a full K8s cluster) |
| CPU     | 4 cores | |
| Disk    | 40 GB free | Docker images are large |
| Network | Internet access | For pulling images |
| Access  | root / sudo | The installer manages system packages |

---

## Architecture (what you're installing)

OpenUBA runs entirely inside a **Kind** (Kubernetes-in-Docker) cluster on the
server:

```
Your workstation browser
        │  SSH tunnel (ports 3000 + 8000)
        ▼
Ubuntu server (<server-ip>)
        │  systemd port-forwards (127.0.0.1 only)
        ▼
Kind cluster (Kubernetes-in-Docker)
  ├── frontend      (Next.js)          :3000
  ├── backend       (FastAPI)          :8000
  ├── postgres      (PostgreSQL)       :5432
  ├── postgraphile  (GraphQL API)      :5000
  ├── elasticsearch (optional)         :9200
  └── spark         (ML jobs)
```

A few facts worth knowing up front:

1. The frontend is built with its API URL baked in at image-build time, so
   remote access is via an **SSH tunnel** (your workstation's `localhost`
   forwards to the server) — see [Remote access](#remote-access).
2. The default admin (`openuba` / `password`) is **seeded by the backend on
   first startup** — there is no separate setup wizard and no manual DB step.
3. Kind binds host ports **80 and 443** for its ingress, so anything already
   on those ports (e.g. nginx) must be stopped before the cluster is created.
   The installer handles this for you.

---

## Option A — Automated install (recommended)

From the server, as root:

```bash
git clone https://github.com/GACWR/OpenUBA.git /opt/openuba
cd /opt/openuba
sudo bash scripts/install-ubuntu.sh
```

The script installs Docker, kubectl, Kind and Node.js; brings up the cluster
with `make reset-dev`; discovers the service names; and wires up reboot-safe
systemd port-forwards (plus an optional nginx proxy). It's safe to re-run from
a clean snapshot.

It's configurable via environment variables (see the header of
`scripts/install-ubuntu.sh`) — for example:

```bash
# skip the nginx proxy and install to a custom location
sudo OPENUBA_DIR=/srv/openuba SETUP_NGINX=false bash scripts/install-ubuntu.sh
```

> Run it against the **system** Python, not inside a `venv` — it manages its
> own dependencies with `--break-system-packages --ignore-installed`.

Then jump to [Remote access](#remote-access).

---

## Option B — Manual install

### 1. System packages

```bash
apt-get update
apt-get install -y curl wget git make jq python3 python3-pip \
    nginx ca-certificates gnupg postgresql-client conntrack socat
```

### 2. Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

### 3. kubectl

```bash
KUBE_VER=$(curl -sL https://dl.k8s.io/release/stable.txt)
curl -sLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBE_VER}/bin/linux/amd64/kubectl"
chmod +x /usr/local/bin/kubectl
```

### 4. Kind

```bash
curl -sLo /usr/local/bin/kind \
    "https://github.com/kubernetes-sigs/kind/releases/download/v0.24.0/kind-linux-amd64"
chmod +x /usr/local/bin/kind
```

### 5. Node.js LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs
```

### 6. Clone and install dependencies

```bash
git clone https://github.com/GACWR/OpenUBA.git /opt/openuba
cd /opt/openuba

# --ignore-installed avoids the urllib3 RECORD-file error on Ubuntu 24.04
pip3 install -r requirements.txt --break-system-packages --ignore-installed

make dev-install-frontend   # a "pnpm not found" warning is fine — it falls back to npm
```

### 7. Bring up the cluster

```bash
# Kind needs ports 80/443 — free them first
systemctl stop nginx

# Creates the cluster, builds images, deploys manifests, seeds the admin user.
# First run takes 10-20 minutes.
make reset-dev
```

`make reset-dev` detects Linux and runs the port-forwards in the background
(logged to `port-forward.log`) — no macOS Terminal is involved.

### 8. Reboot-safe port-forwards

The cluster is only reachable from inside the server until you expose it.
Create a systemd unit per service (discover the real names first with
`kubectl get svc -n openuba`):

```bash
cat > /etc/systemd/system/openuba-pf-frontend.service <<'EOF'
[Unit]
Description=OpenUBA frontend port-forward
After=network.target
[Service]
Type=simple
ExecStart=/usr/local/bin/kubectl port-forward --namespace=openuba --address=127.0.0.1 svc/frontend 3000:3000
Restart=on-failure
RestartSec=5s
Environment=KUBECONFIG=/root/.kube/config
[Install]
WantedBy=multi-user.target
EOF
# repeat for backend (8000) and postgres (5432)

systemctl daemon-reload
systemctl enable --now openuba-pf-frontend openuba-pf-backend openuba-pf-postgres
systemctl start nginx    # optional convenience proxy
```

---

## Remote access

Because the frontend was compiled with a `localhost` API URL, use an SSH
tunnel from your workstation — direct browser access to `http://<server-ip>:3000`
loads the page but its API calls fail.

**Linux / macOS:**

```bash
ssh -N -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 user@<server-ip>
```

**Windows (PowerShell):**

```powershell
ssh -N `
  -L 3000:127.0.0.1:3000 `
  -L 8000:127.0.0.1:8000 `
  user@<server-ip>
```

Keep the terminal open, then browse to <http://localhost:3000>.

---

## Default credentials

```
Username: openuba
Password: password
```

> ⚠️ Change this immediately after first login (**Settings → Users**). These
> are seeded by the backend on first startup — don't try to create a user via
> `psql` beforehand.

---

## Known issues & fixes

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot uninstall urllib3 … RECORD file not found` | Ubuntu ships `urllib3` as a Debian package with no pip RECORD file | Install with `pip3 install --ignore-installed` (the script does this) |
| `failed to bind host port 0.0.0.0:80/tcp: address already in use` | Kind's ingress binds 80/443; nginx is already there | Stop nginx before `make reset-dev` (the script does this) |
| Login shows **"Failed to fetch"** | The browser is trying to reach `localhost:8000` on your workstation | SSH-tunnel **both** 3000 and 8000 (see [Remote access](#remote-access)) |
| `elastic_transport.ConnectionError` in backend logs | Elasticsearch is slower to become ready than the backend expects | Non-critical — login, alerts and rules work without it |
| `osascript` / "Terminal.app" error | Older releases launched port-forwards via a macOS-only command | Fixed — `scripts/start-dev.sh` now detects Linux and backgrounds them |

---

## Verification

```bash
kubectl get pods -n openuba                     # all pods Running
systemctl status openuba-pf-frontend --no-pager # active
curl -I http://127.0.0.1:3000                   # HTTP 200
curl -I http://127.0.0.1:8000/docs              # HTTP 200
```

## Diagnostics

| Problem | Command |
|---|---|
| Pod not starting | `kubectl describe pod -n openuba <pod>` |
| Backend errors | `kubectl logs -n openuba deploy/backend -f` |
| Port-forward died | `systemctl restart openuba-pf-frontend` |
| Full cluster rebuild (destructive) | `cd /opt/openuba && make reset-dev` |
