#!/usr/bin/env bash
# =============================================================================
# OpenUBA — automated install for Ubuntu Server (22.04 / 24.04)
#
# Installs Docker, kubectl, Kind, and Node.js, then brings up the full OpenUBA
# stack in a local Kind cluster and exposes it via persistent (reboot-safe)
# port-forwards. Idempotent enough to re-run from a clean snapshot.
#
# Based on the community install guide contributed in issue #116 (thanks to
# @rock0ne). See docs/INSTALL_UBUNTU.md for the manual walkthrough, the known
# issues behind each step, and remote-access instructions.
#
# Usage:
#   sudo bash scripts/install-ubuntu.sh          # run from a fresh clone, or
#   curl -fsSL <raw-url>/scripts/install-ubuntu.sh | sudo bash
#
# Configuration (override via environment):
#   OPENUBA_DIR   install location            (default: /opt/openuba)
#   OPENUBA_REPO  git remote to clone          (default: upstream GACWR/OpenUBA)
#   OPENUBA_REF   branch/tag to check out      (default: master)
#   K8S_NS        kubernetes namespace         (default: openuba)
#   KIND_VER      pinned Kind release          (default: v0.24.0)
#   SETUP_NGINX   install convenience proxy    (default: true)
# =============================================================================
set -euo pipefail

OPENUBA_DIR="${OPENUBA_DIR:-/opt/openuba}"
OPENUBA_REPO="${OPENUBA_REPO:-https://github.com/GACWR/OpenUBA.git}"
OPENUBA_REF="${OPENUBA_REF:-master}"
K8S_NS="${K8S_NS:-openuba}"
KIND_VER="${KIND_VER:-v0.24.0}"
SETUP_NGINX="${SETUP_NGINX:-true}"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERR]${NC}   $*" >&2; exit 1; }

# ─── 0. Preflight ────────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && die "Run as root: sudo bash $0"
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[[ -z "$HOST_IP" ]] && HOST_IP="<server-ip>"

# ─── 1. System packages ──────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    curl wget git make jq python3 python3-pip \
    ca-certificates gnupg lsb-release \
    postgresql-client conntrack socat
[[ "$SETUP_NGINX" == "true" ]] && apt-get install -y -qq nginx

# ─── 2. Docker ───────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
    [[ -n "${SUDO_USER:-}" ]] && usermod -aG docker "$SUDO_USER"
fi
ok "Docker: $(docker --version)"

# ─── 3. kubectl ──────────────────────────────────────────────────────────────
if ! command -v kubectl &>/dev/null; then
    info "Installing kubectl..."
    KUBE_VER="$(curl -sL --max-time 10 https://dl.k8s.io/release/stable.txt 2>/dev/null || echo "v1.31.0")"
    [[ -z "$KUBE_VER" ]] && KUBE_VER="v1.31.0"
    curl -sLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBE_VER}/bin/linux/amd64/kubectl"
    chmod +x /usr/local/bin/kubectl
fi
ok "kubectl: $(kubectl version --client 2>/dev/null | head -1)"

# ─── 4. Kind ─────────────────────────────────────────────────────────────────
if ! command -v kind &>/dev/null; then
    info "Installing Kind ${KIND_VER} (pinned to avoid GitHub API rate limits)..."
    curl -sLo /usr/local/bin/kind "https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VER}/kind-linux-amd64"
    chmod +x /usr/local/bin/kind
fi
ok "Kind: $(kind version)"

# ─── 5. Node.js LTS ──────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    info "Installing Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
fi
ok "Node: $(node --version) / npm: $(npm --version)"

# ─── 6. Clone / update the repo ──────────────────────────────────────────────
if [[ -d "$OPENUBA_DIR/.git" ]]; then
    info "Updating existing checkout in $OPENUBA_DIR..."
    git -C "$OPENUBA_DIR" fetch --depth 1 origin "$OPENUBA_REF"
    git -C "$OPENUBA_DIR" checkout "$OPENUBA_REF"
    git -C "$OPENUBA_DIR" reset --hard "origin/$OPENUBA_REF" 2>/dev/null || true
else
    info "Cloning OpenUBA into $OPENUBA_DIR..."
    git clone --branch "$OPENUBA_REF" "$OPENUBA_REPO" "$OPENUBA_DIR"
fi
cd "$OPENUBA_DIR"
ok "Repo ready at $OPENUBA_DIR ($OPENUBA_REF)."

# ─── 7. Python dependencies ──────────────────────────────────────────────────
# --ignore-installed avoids pip aborting on Debian-managed packages (e.g.
# urllib3) that ship without a RECORD file and cannot be cleanly uninstalled.
info "Installing Python dependencies..."
pip3 install -r requirements.txt --break-system-packages --ignore-installed -q
ok "Python deps installed."

# ─── 8. Frontend dependencies ────────────────────────────────────────────────
info "Installing frontend dependencies..."
make dev-install-frontend
ok "Frontend deps installed."

# ─── 9. Free ports 80/443 for the Kind ingress ───────────────────────────────
# configs/local.yaml binds 80/443 on the host; stop nginx first so cluster
# creation doesn't fail with "address already in use". We restart it later.
if [[ "$SETUP_NGINX" == "true" ]]; then
    info "Stopping nginx to free ports 80/443 for cluster creation..."
    systemctl stop nginx 2>/dev/null || true
fi

# ─── 10. Build & deploy the cluster ──────────────────────────────────────────
# start-dev.sh detects Linux and runs port-forwards in the background (no
# macOS Terminal.app dependency), so no source patching is needed here.
info "Running make reset-dev (10-20 min on first run)..."
make reset-dev
ok "Cluster deployed. The backend seeds the default admin (openuba / password) on first startup."

# ─── 11. Discover service + deployment names (no hardcoding) ──────────────────
info "Discovering services in namespace $K8S_NS..."
kubectl get svc -n "$K8S_NS" || true

svc_by_port() { kubectl get svc -n "$K8S_NS" -o json | jq -r --argjson p "$1" '.items[] | select(.spec.ports[]?.port == $p) | .metadata.name' | head -1; }
svc_by_name() { kubectl get svc -n "$K8S_NS" --no-headers -o custom-columns=NAME:.metadata.name | grep -i "$1" | grep -iv graphile | head -1; }
deploy_by_name() { kubectl get deploy -n "$K8S_NS" --no-headers -o custom-columns=NAME:.metadata.name | grep -i "$1" | head -1; }

FRONTEND_SVC="$(svc_by_port 3000)"; [[ -z "$FRONTEND_SVC" ]] && FRONTEND_SVC="$(svc_by_name front)"
BACKEND_SVC="$(svc_by_port 8000)";  [[ -z "$BACKEND_SVC"  ]] && BACKEND_SVC="$(svc_by_name back)"
POSTGRES_SVC="$(svc_by_port 5432)"; [[ -z "$POSTGRES_SVC" ]] && POSTGRES_SVC="$(svc_by_name post)"
BACKEND_DEPLOY="$(deploy_by_name back)"
FRONTEND_DEPLOY="$(deploy_by_name front)"

[[ -z "$FRONTEND_SVC"    ]] && die "Cannot find frontend service. Check: kubectl get svc -n $K8S_NS"
[[ -z "$BACKEND_SVC"     ]] && die "Cannot find backend service. Check: kubectl get svc -n $K8S_NS"
[[ -z "$BACKEND_DEPLOY"  ]] && die "Cannot find backend deployment."
[[ -z "$FRONTEND_DEPLOY" ]] && die "Cannot find frontend deployment."
ok "Frontend svc=$FRONTEND_SVC deploy=$FRONTEND_DEPLOY | Backend svc=$BACKEND_SVC deploy=$BACKEND_DEPLOY"

# ─── 12. Wait for rollouts ───────────────────────────────────────────────────
info "Waiting for backend + frontend rollouts..."
kubectl rollout status -n "$K8S_NS" "deploy/$BACKEND_DEPLOY"  --timeout=600s
kubectl rollout status -n "$K8S_NS" "deploy/$FRONTEND_DEPLOY" --timeout=600s
kubectl get pods -n "$K8S_NS"

# ─── 13. Persistent systemd port-forwards (127.0.0.1, survive reboot) ─────────
info "Creating systemd port-forward services..."
write_pf_unit() {
    local name="$1" svc="$2" local_port="$3" remote_port="$4"
    cat > "/etc/systemd/system/openuba-pf-${name}.service" <<EOF
[Unit]
Description=OpenUBA kubectl port-forward ${svc} ${local_port}:${remote_port}
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/kubectl port-forward --namespace=${K8S_NS} --address=127.0.0.1 svc/${svc} ${local_port}:${remote_port}
Restart=on-failure
RestartSec=5s
Environment=KUBECONFIG=/root/.kube/config

[Install]
WantedBy=multi-user.target
EOF
}
write_pf_unit frontend "$FRONTEND_SVC" 3000 3000
write_pf_unit backend  "$BACKEND_SVC"  8000 8000
write_pf_unit postgres "$POSTGRES_SVC" 5432 5432
systemctl daemon-reload
systemctl enable --now openuba-pf-frontend openuba-pf-backend openuba-pf-postgres
ok "Systemd port-forward services active."

# ─── 14. Nginx convenience proxy ─────────────────────────────────────────────
if [[ "$SETUP_NGINX" == "true" ]]; then
    info "Configuring nginx convenience proxy..."
    cat > /etc/nginx/sites-available/openuba <<'NGINX'
upstream openuba_frontend { server 127.0.0.1:3000; }
upstream openuba_backend  { server 127.0.0.1:8000; }

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass         http://openuba_frontend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }

    location /api/ {
        proxy_pass         http://openuba_backend/;
        proxy_http_version 1.1;
        proxy_set_header   Host            $host;
        proxy_set_header   X-Real-IP       $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/openuba /etc/nginx/sites-enabled/openuba
    nginx -t && systemctl enable --now nginx && systemctl reload nginx
    ok "nginx running."
fi

# ─── 15. Smoke test ──────────────────────────────────────────────────────────
info "Running smoke tests..."
sleep 3
FRONTEND_HTTP="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000 || echo 000)"
BACKEND_HTTP="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/docs || echo 000)"
[[ "$FRONTEND_HTTP" =~ ^(200|301|302|304)$ ]] && ok "Frontend responding: HTTP $FRONTEND_HTTP" || warn "Frontend not responding yet (HTTP $FRONTEND_HTTP) — may still be starting"
[[ "$BACKEND_HTTP"  =~ ^(200|301|302|304)$ ]] && ok "Backend responding: HTTP $BACKEND_HTTP"   || warn "Backend not responding yet (HTTP $BACKEND_HTTP) — may still be starting"

# ─── 16. Summary ─────────────────────────────────────────────────────────────
cat <<SUMMARY

$(echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}")
$(echo -e "${GREEN}  OpenUBA install complete${NC}")
$(echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}")

  Default login:  openuba / password   (change it: Settings → Users)

  Remote access — SSH tunnel from your workstation (recommended):
    ssh -N -L 3000:127.0.0.1:3000 -L 8000:127.0.0.1:8000 user@${HOST_IP}
  then open http://localhost:3000

  Convenience (nginx, if enabled):  http://${HOST_IP}/

  Diagnostics:
    kubectl get pods -n ${K8S_NS}
    kubectl logs -n ${K8S_NS} deploy/${BACKEND_DEPLOY} -f
    systemctl status openuba-pf-frontend openuba-pf-backend

  Full guide: docs/INSTALL_UBUNTU.md
SUMMARY
