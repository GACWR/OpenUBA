#!/usr/bin/env python3
"""
OpenUBA v2 Architecture Diagram Generator

Generates an SVG architecture diagram matching the v1 framework.jpg style:
white background, dashed-border grouping boxes, technology labels, clean arrows.

All edges use orthogonal (elbow) routing to avoid overlapping text/boxes.

Usage: python3 images/diagram/generate.py
Output: images/diagram/architecture.svg
"""

import os
import svgwrite

# ─── Canvas ───────────────────────────────────────────────────────────
W, H = 1500, 1100
OUT = os.path.join(os.path.dirname(__file__), "architecture.svg")

dwg = svgwrite.Drawing(OUT, size=(W, H), profile="full")
dwg.add(dwg.rect(insert=(0, 0), size=(W, H), fill="white"))

# ─── Style constants ─────────────────────────────────────────────────
FONT = "Helvetica, Arial, sans-serif"
TITLE_SIZE = 16
SUBTITLE_SIZE = 13
BODY_SIZE = 11
SMALL_SIZE = 10

# Colors
C_FRONTEND = "#e8f4fd"
C_FRONTEND_BD = "#2196F3"
C_BACKEND = "#e8f5e9"
C_BACKEND_BD = "#4CAF50"
C_DATA = "#fff3e0"
C_DATA_BD = "#FF9800"
C_EXEC = "#f3e5f5"
C_EXEC_BD = "#9C27B0"
C_EXTERNAL = "#fafafa"
C_EXTERNAL_BD = "#9E9E9E"
C_K8S = "#f5f5f5"
C_K8S_BD = "#616161"
C_ARROW = "#424242"
C_ARROW_DASH = "#9E9E9E"
C_TITLE = "#212121"
C_BODY = "#424242"
C_MUTED = "#757575"

_marker_id = 0


# ─── Helper functions ─────────────────────────────────────────────────

def _next_marker_id():
    global _marker_id
    _marker_id += 1
    return f"m{_marker_id}"


def _make_markers(color, forward=True, reverse=False):
    """Create arrow markers and return (fwd_marker, rev_marker) or None."""
    fwd = rev = None
    if forward:
        mid = _next_marker_id()
        fwd = dwg.marker(id=mid, insert=(6, 3), size=(8, 6),
                         orient="auto", markerUnits="strokeWidth")
        fwd.add(dwg.path(d="M0,0 L6,3 L0,6 Z", fill=color))
        dwg.defs.add(fwd)
    if reverse:
        mid = _next_marker_id()
        rev = dwg.marker(id=mid, insert=(0, 3), size=(8, 6),
                         orient="auto", markerUnits="strokeWidth")
        rev.add(dwg.path(d="M6,0 L0,3 L6,6 Z", fill=color))
        dwg.defs.add(rev)
    return fwd, rev


def dashed_box(x, y, w, h, fill, stroke, title, title_underline=True, rx=8):
    g = dwg.g()
    g.add(dwg.rect(
        insert=(x, y), size=(w, h),
        fill=fill, stroke=stroke,
        stroke_width=2, stroke_dasharray="8,4",
        rx=rx, ry=rx
    ))
    if title:
        g.add(dwg.text(
            title, insert=(x + w / 2, y + 22),
            font_family=FONT, font_size=TITLE_SIZE,
            font_weight="bold", fill=C_TITLE,
            text_anchor="middle",
            text_decoration="underline" if title_underline else "none"
        ))
    return g


def solid_box(x, y, w, h, fill, stroke, rx=6):
    return dwg.rect(
        insert=(x, y), size=(w, h),
        fill=fill, stroke=stroke,
        stroke_width=1.5, rx=rx, ry=rx
    )


def text(x, y, label, size=BODY_SIZE, weight="normal", fill=C_BODY, anchor="middle"):
    return dwg.text(
        label, insert=(x, y),
        font_family=FONT, font_size=size,
        font_weight=weight, fill=fill,
        text_anchor=anchor
    )


def label_with_bg(x, y, label, size=SMALL_SIZE, fill=C_MUTED, pad_x=4, pad_y=3):
    """Draw a text label with a white background rect for readability."""
    g = dwg.g()
    # Estimate text width (rough: size * 0.55 * len)
    tw = size * 0.55 * len(label)
    th = size + 2
    g.add(dwg.rect(
        insert=(x - tw / 2 - pad_x, y - th + pad_y - 1),
        size=(tw + pad_x * 2, th + pad_y),
        fill="white", fill_opacity=0.92, rx=2, ry=2
    ))
    g.add(dwg.text(
        label, insert=(x, y),
        font_family=FONT, font_size=size,
        fill=fill, text_anchor="middle"
    ))
    return g


def elbow_path(points, dashed=False, color=None, bidi=False, label=None,
               label_seg=None, label_side="above"):
    """
    Draw an orthogonal (elbow) arrow through a list of (x,y) waypoints.
    points: list of (x, y) tuples — at least 2 points
    label_seg: which segment index to place the label on (0-based), default middle
    label_side: "above" or "below" — offset direction for the label
    """
    c = color or (C_ARROW_DASH if dashed else C_ARROW)
    g = dwg.g()

    # Build SVG path
    d = f"M{points[0][0]},{points[0][1]}"
    for px, py in points[1:]:
        d += f" L{px},{py}"

    path_attrs = {"stroke": c, "stroke_width": 1.5, "fill": "none"}
    if dashed:
        path_attrs["stroke_dasharray"] = "6,3"

    path = dwg.path(d=d, **path_attrs)

    # Markers
    fwd, rev = _make_markers(c, forward=True, reverse=bidi)
    path["marker-end"] = fwd.get_funciri()
    if bidi and rev:
        path["marker-start"] = rev.get_funciri()
    g.add(path)

    # Label
    if label:
        if label_seg is None:
            label_seg = len(points) // 2 - 1
        label_seg = max(0, min(label_seg, len(points) - 2))
        p1 = points[label_seg]
        p2 = points[label_seg + 1]
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        # Offset label to avoid sitting on the line
        if p1[1] == p2[1]:  # horizontal segment
            offset = -10 if label_side == "above" else 14
            my += offset
        else:  # vertical segment
            offset = -8 if label_side == "above" else 8
            # For vertical, place label to the side
            mx += offset
            # Rotate label for vertical? No, keep horizontal but offset
            mx += 0
        g.add(label_with_bg(mx, my, label))
    return g


def component_box(x, y, w, h, label, sublabel=None, fill="#ffffff", stroke="#bdbdbd"):
    g = dwg.g()
    g.add(solid_box(x, y, w, h, fill, stroke))
    g.add(text(x + w / 2, y + h / 2 + 4, label, size=BODY_SIZE, weight="bold", fill=C_TITLE))
    if sublabel:
        g.add(text(x + w / 2, y + h / 2 + 17, sublabel, size=SMALL_SIZE, fill=C_MUTED))
    return g


# ─── Main title ───────────────────────────────────────────────────────
dwg.add(text(W / 2, 30, "OpenUBA v0.0.2 \u2014 Architecture",
             size=22, weight="bold", fill="#1a1a1a"))
dwg.add(text(W / 2, 48, "User & Entity Behavior Analytics Platform",
             size=12, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# LAYOUT COORDINATES
# ═══════════════════════════════════════════════════════════════════════
# Frontend
FE_X, FE_Y, FE_W, FE_H = 280, 65, 860, 120

# K8s cluster
K8S_X, K8S_Y, K8S_W, K8S_H = 60, 230, 1380, 570

# Backend API
BE_X, BE_Y, BE_W, BE_H = 90, 268, 520, 235

# PostGraphile
PG_X, PG_Y, PG_W, PG_H = 640, 268, 200, 100

# Operator
OP_X, OP_Y, OP_W, OP_H = 640, 395, 200, 95

# Data Layer
DL_X, DL_Y, DL_W, DL_H = 90, 555, 520, 225

# Execution Plane
EX_X, EX_Y, EX_W, EX_H = 870, 268, 550, 340

# LLM Providers (below K8s, right)
LLM_X, LLM_Y, LLM_W, LLM_H = 640, 830, 280, 110

# Security Analysts (below K8s, far right)
UA_X, UA_Y, UA_W, UA_H = 960, 830, 250, 110

# Model Registries (below K8s, left)
MR_X, MR_Y, MR_W, MR_H = 60, 830, 250, 110

# SIEM (below K8s, center-left)
SIEM_X, SIEM_Y, SIEM_W, SIEM_H = 340, 830, 160, 110


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: FRONTEND
# ═══════════════════════════════════════════════════════════════════════
dwg.add(dashed_box(FE_X, FE_Y, FE_W, FE_H, C_FRONTEND, C_FRONTEND_BD, "Frontend"))

dwg.add(text(FE_X + 80, FE_Y + 50, "Next.js 14", size=SUBTITLE_SIZE, weight="bold"))
dwg.add(text(FE_X + 80, FE_Y + 66, "React 18 / TypeScript", size=SMALL_SIZE, fill=C_MUTED))
dwg.add(text(FE_X + 80, FE_Y + 80, "TailwindCSS / shadcn", size=SMALL_SIZE, fill=C_MUTED))

pages = ["Dashboard", "Models", "Anomalies", "Cases", "Data", "Settings"]
for i, page in enumerate(pages):
    bx = FE_X + 200 + i * 88
    dwg.add(solid_box(bx, FE_Y + 42, 80, 24, "#ffffff", C_FRONTEND_BD, rx=4))
    dwg.add(text(bx + 40, FE_Y + 58, page, size=9, fill=C_FRONTEND_BD))

# LLM Chat + Auth
dwg.add(solid_box(FE_X + 740, FE_Y + 42, 65, 24, "#ffffff", C_FRONTEND_BD, rx=4))
dwg.add(text(FE_X + 772, FE_Y + 58, "LLM Chat", size=9, fill=C_FRONTEND_BD))
dwg.add(solid_box(FE_X + 810, FE_Y + 42, 65, 24, "#ffffff", C_FRONTEND_BD, rx=4))
dwg.add(text(FE_X + 842, FE_Y + 58, "Auth/RBAC", size=9, fill=C_FRONTEND_BD))

dwg.add(text(FE_X + 220, FE_Y + 100,
             "Recharts / Apollo Client / Zustand / GraphQL Subscriptions",
             size=9, fill=C_MUTED, anchor="start"))


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: KUBERNETES CLUSTER
# ═══════════════════════════════════════════════════════════════════════
dwg.add(dashed_box(K8S_X, K8S_Y, K8S_W, K8S_H, C_K8S, C_K8S_BD,
                   "Kubernetes Cluster (Kind / Production)"))

# ── 2a: Backend API ──────────────────────────────────────────────────
dwg.add(dashed_box(BE_X, BE_Y, BE_W, BE_H, C_BACKEND, C_BACKEND_BD, "Backend API"))
dwg.add(component_box(BE_X + 15, BE_Y + 35, 230, 45, "FastAPI",
                       "Uvicorn ASGI / REST API"))

services = [
    ("Auth", "JWT / RBAC"),
    ("Model Orchestrator", None),
    ("Rule Engine", None),
    ("Scheduler", "APScheduler"),
    ("Chat Service", "SSE Streaming"),
    ("Notifications", None),
]
sx, sy = BE_X + 15, BE_Y + 95
for i, (svc, sub) in enumerate(services):
    col = i % 3
    row = i // 3
    bx = sx + col * 165
    by = sy + row * 55
    h = 40 if sub else 28
    dwg.add(solid_box(bx, by, 155, h, "#ffffff", C_BACKEND_BD, rx=4))
    dwg.add(text(bx + 78, by + 14, svc, size=10, weight="bold", fill="#2E7D32"))
    if sub:
        dwg.add(text(bx + 78, by + 28, sub, size=9, fill=C_MUTED))

# ── 2b: PostGraphile ────────────────────────────────────────────────
dwg.add(dashed_box(PG_X, PG_Y, PG_W, PG_H, "#e3f2fd", "#1565C0", "PostGraphile"))
dwg.add(text(PG_X + PG_W / 2, PG_Y + 50, "GraphQL Auto-Schema",
             size=10, fill="#1565C0"))
dwg.add(text(PG_X + PG_W / 2, PG_Y + 66, "from PostgreSQL",
             size=10, fill=C_MUTED))
dwg.add(text(PG_X + PG_W / 2, PG_Y + 82, "Subscriptions / Mutations",
             size=9, fill=C_MUTED))

# ── 2c: Operator ────────────────────────────────────────────────────
dwg.add(dashed_box(OP_X, OP_Y, OP_W, OP_H, "#fce4ec", "#c62828",
                   "OpenUBA Operator"))
dwg.add(text(OP_X + OP_W / 2, OP_Y + 48, "Kopf Framework",
             size=10, fill="#c62828"))
dwg.add(text(OP_X + OP_W / 2, OP_Y + 64, "Watches CRDs:",
             size=9, fill=C_MUTED))
dwg.add(text(OP_X + OP_W / 2, OP_Y + 78, "UBATraining / UBAInference",
             size=9, fill="#c62828"))

# ── 2d: Data Layer ──────────────────────────────────────────────────
dwg.add(dashed_box(DL_X, DL_Y, DL_W, DL_H, C_DATA, C_DATA_BD, "Data Layer"))

# PostgreSQL
dwg.add(component_box(DL_X + 15, DL_Y + 38, 155, 48,
                       "PostgreSQL 15", "System of Record"))
dwg.add(text(DL_X + 92, DL_Y + 100, "Models / Runs / Anomalies",
             size=8, fill=C_MUTED))
dwg.add(text(DL_X + 92, DL_Y + 111, "Cases / Rules / Users / Logs",
             size=8, fill=C_MUTED))

# Elasticsearch
dwg.add(component_box(DL_X + 185, DL_Y + 38, 155, 48,
                       "Elasticsearch 8.x", "Search & Analytics"))
dwg.add(text(DL_X + 262, DL_Y + 100, "Event Indexing / Anomalies",
             size=8, fill=C_MUTED))
dwg.add(text(DL_X + 262, DL_Y + 111, "Kibana Dashboards",
             size=8, fill=C_MUTED))

# Spark
dwg.add(component_box(DL_X + 355, DL_Y + 38, 155, 48,
                       "Apache Spark", "Distributed Compute"))
dwg.add(text(DL_X + 432, DL_Y + 100, "PySpark / MLlib",
             size=8, fill=C_MUTED))
dwg.add(text(DL_X + 432, DL_Y + 111, "Master + Worker Pods",
             size=8, fill=C_MUTED))

# PVCs
dwg.add(text(DL_X + DL_W / 2, DL_Y + 140, "Persistent Volumes",
             size=SUBTITLE_SIZE, weight="bold", fill=C_DATA_BD))
pvcs = ["model-storage", "saved-models", "datasets",
        "system-storage", "postgres", "elasticsearch"]
for i, pvc in enumerate(pvcs):
    bx = DL_X + 20 + i * 83
    by = DL_Y + 155
    dwg.add(solid_box(bx, by, 78, 22, "#fff8e1", C_DATA_BD, rx=3))
    dwg.add(text(bx + 39, by + 15, pvc, size=7, fill="#E65100"))

# ── 2e: Execution Plane ─────────────────────────────────────────────
dwg.add(dashed_box(EX_X, EX_Y, EX_W, EX_H, C_EXEC, C_EXEC_BD,
                   "Model Execution Plane"))
dwg.add(text(EX_X + EX_W / 2, EX_Y + 45, "Ephemeral K8s Jobs (JIT)",
             size=11, fill=C_EXEC_BD))

runtimes = [
    ("sklearn", "scikit-learn / joblib"),
    ("pytorch", "PyTorch / torch.save"),
    ("tensorflow", "TensorFlow / SavedModel"),
    ("networkx", "NetworkX / graph analytics"),
]
for i, (rt, desc) in enumerate(runtimes):
    col = i % 2
    row = i // 2
    bx = EX_X + 25 + col * 260
    by = EX_Y + 58 + row * 82
    dwg.add(solid_box(bx, by, 245, 68, "#ffffff", C_EXEC_BD, rx=6))
    dwg.add(text(bx + 122, by + 20, f"model-runner:{rt}",
                 size=11, weight="bold", fill="#6A1B9A"))
    dwg.add(text(bx + 122, by + 38, desc, size=9, fill=C_MUTED))
    dwg.add(text(bx + 122, by + 55, "Docker Container",
                 size=8, fill="#9E9E9E"))

# Model Library + Artifact Storage
dwg.add(solid_box(EX_X + 25, EX_Y + 235, 245, 50, "#f3e5f5", C_EXEC_BD, rx=6))
dwg.add(text(EX_X + 147, EX_Y + 256, "Model Library",
             size=12, weight="bold", fill="#6A1B9A"))
dwg.add(text(EX_X + 147, EX_Y + 273, "Installed models + manifests + hashes",
             size=9, fill=C_MUTED))

dwg.add(solid_box(EX_X + 285, EX_Y + 235, 245, 50, "#f3e5f5", C_EXEC_BD, rx=6))
dwg.add(text(EX_X + 407, EX_Y + 256, "Artifact Storage",
             size=12, weight="bold", fill="#6A1B9A"))
dwg.add(text(EX_X + 407, EX_Y + 273, "Trained checkpoints / metrics",
             size=9, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: EXTERNAL BOXES (below K8s cluster)
# ═══════════════════════════════════════════════════════════════════════

# Model Registries
dwg.add(dashed_box(MR_X, MR_Y, MR_W, MR_H, C_EXTERNAL, C_EXTERNAL_BD,
                   "Model Registries"))
for i, reg in enumerate(["GitHub", "OpenUBA Hub", "HuggingFace", "Local FS"]):
    col = i % 2
    row = i // 2
    rx = MR_X + 15 + col * 120
    ry = MR_Y + 35 + row * 30
    dwg.add(solid_box(rx, ry, 110, 24, "#ffffff", "#9E9E9E", rx=4))
    dwg.add(text(rx + 55, ry + 16, reg, size=10, fill=C_BODY))

# SIEM
dwg.add(dashed_box(SIEM_X, SIEM_Y, SIEM_W, SIEM_H, "#e8eaf6", "#3F51B5", "SIEM"))
dwg.add(text(SIEM_X + SIEM_W / 2, SIEM_Y + 50, "Any SIEM Platform",
             size=10, fill="#3F51B5"))
dwg.add(text(SIEM_X + SIEM_W / 2, SIEM_Y + 66, "Splunk / QRadar / etc.",
             size=9, fill=C_MUTED))
dwg.add(text(SIEM_X + SIEM_W / 2, SIEM_Y + 82, "SIEM-Agnostic Design",
             size=9, fill=C_MUTED))

# LLM Providers
dwg.add(dashed_box(LLM_X, LLM_Y, LLM_W, LLM_H, "#e0f7fa", "#00838F",
                   "LLM Providers"))
for i, prov in enumerate(["Ollama (Local)", "OpenAI", "Claude", "Gemini"]):
    col = i % 2
    row = i // 2
    px = LLM_X + 20 + col * 130
    py = LLM_Y + 35 + row * 30
    dwg.add(solid_box(px, py, 120, 24, "#ffffff", "#00838F", rx=4))
    dwg.add(text(px + 60, py + 16, prov, size=10, fill="#00838F"))

# Security Analysts
dwg.add(dashed_box(UA_X, UA_Y, UA_W, UA_H, "#efebe9", "#5D4037",
                   "Security Analysts"))
for i, role in enumerate(["Admin", "Manager", "Triage", "Analyst"]):
    rx = UA_X + 18 + i * 57
    ry = UA_Y + 38
    dwg.add(solid_box(rx, ry, 52, 22, "#ffffff", "#5D4037", rx=4))
    dwg.add(text(rx + 26, ry + 15, role, size=9, fill="#5D4037"))
dwg.add(text(UA_X + UA_W / 2, UA_Y + 80, "Role-Based Access Control",
             size=10, fill="#5D4037"))
dwg.add(text(UA_X + UA_W / 2, UA_Y + 94, "JWT Authentication",
             size=9, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# EDGES — All orthogonal (elbow) routed
# ═══════════════════════════════════════════════════════════════════════

# --- 1. Frontend ↔ Backend (REST / SSE) ---
# Vertical drop from FE bottom to BE top
fe_be_x = 400
dwg.add(elbow_path(
    [(fe_be_x, FE_Y + FE_H), (fe_be_x, BE_Y)],
    bidi=True, label="REST / SSE", label_seg=0, label_side="above"
))

# --- 2. Frontend ↔ PostGraphile (GraphQL) ---
# Vertical drop
fe_pg_x = PG_X + PG_W / 2
dwg.add(elbow_path(
    [(fe_pg_x, FE_Y + FE_H), (fe_pg_x, PG_Y)],
    bidi=True, label="GraphQL", label_seg=0, label_side="above"
))

# --- 3. Frontend ↔ Security Analysts (Browser) ---
# Route OUTSIDE K8s: go right from FE, down right margin, into Analysts
analyst_cx = UA_X + UA_W / 2
route_x = K8S_X + K8S_W + 20  # right of K8s cluster
dwg.add(elbow_path(
    [(FE_X + FE_W, FE_Y + FE_H / 2),
     (route_x, FE_Y + FE_H / 2),
     (route_x, UA_Y + UA_H / 2),
     (UA_X + UA_W, UA_Y + UA_H / 2)],
    bidi=True, dashed=True, label="Browser",
    label_seg=1, label_side="above"
))

# --- 4. Backend ↔ PostgreSQL (SQLAlchemy) ---
# Vertical drop through the gap between backend bottom and data top
pg_x = BE_X + 92
dwg.add(elbow_path(
    [(pg_x, BE_Y + BE_H), (pg_x, DL_Y + 38)],
    bidi=True, label="SQLAlchemy", label_seg=0
))

# --- 5. Backend ↔ Elasticsearch (HTTP) ---
es_x = BE_X + 262
dwg.add(elbow_path(
    [(es_x, BE_Y + BE_H), (es_x, DL_Y + 38)],
    bidi=True, label="HTTP", label_seg=0
))

# --- 6. Backend ↔ Spark (PySpark) ---
sp_x = BE_X + 432
dwg.add(elbow_path(
    [(sp_x, BE_Y + BE_H), (sp_x, DL_Y + 38)],
    bidi=True, label="PySpark", label_seg=0
))

# --- 7. PostGraphile ↔ PostgreSQL (Introspection) ---
# Elbow: down from PG bottom, left along the gap, then down into PG box in data
gap_y = DL_Y - 8  # horizontal routing channel between sections
dwg.add(elbow_path(
    [(PG_X + 40, PG_Y + PG_H),
     (PG_X + 40, gap_y),
     (DL_X + 140, gap_y),
     (DL_X + 140, DL_Y + 38)],
    bidi=True, dashed=True, label="Introspection",
    label_seg=1, label_side="above"
))

# --- 8. Backend → Operator (Creates CRDs) ---
# Horizontal from backend right edge to operator left edge
crd_y = OP_Y + 30
dwg.add(elbow_path(
    [(BE_X + BE_W, crd_y), (OP_X, crd_y)],
    label="Creates CRDs", label_seg=0, label_side="above"
))

# --- 9. Operator → Model Runners (Creates Jobs) ---
# Horizontal from operator right to execution plane left
job_y = OP_Y + 55
dwg.add(elbow_path(
    [(OP_X + OP_W, job_y), (EX_X, job_y)],
    label="Creates Jobs", label_seg=0, label_side="above"
))

# --- 10. Backend → Execution Plane (Train / Infer API) ---
# Horizontal at top: from backend right, across to execution plane left
# Route above operator/postgraphile via elbow
api_y = BE_Y + 50
dwg.add(elbow_path(
    [(BE_X + BE_W, api_y),
     (BE_X + BE_W + 15, api_y),
     (BE_X + BE_W + 15, K8S_Y + 28),
     (EX_X + EX_W / 2, K8S_Y + 28),
     (EX_X + EX_W / 2, EX_Y)],
    label="Train / Infer API", label_seg=2, label_side="below"
))

# --- 11. Runners → PostgreSQL (Direct SQL for logs/results) ---
# Elbow: down from execution bottom, left along bottom channel, up into data
route_y = DL_Y + DL_H + 8  # just below data layer
dwg.add(elbow_path(
    [(EX_X + 60, EX_Y + EX_H),
     (EX_X + 60, route_y),
     (DL_X + 60, route_y),
     (DL_X + 60, DL_Y + DL_H)],
    dashed=True, label="Direct SQL (logs / results)",
    label_seg=1, label_side="below"
))

# --- 12. Model Registries → Backend (Install Models) ---
# Up from registries top, into backend bottom-left
mr_top_x = MR_X + MR_W / 2
dwg.add(elbow_path(
    [(mr_top_x, MR_Y),
     (mr_top_x, DL_Y + DL_H + 8),
     (DL_X + 30, DL_Y + DL_H + 8),
     (DL_X + 30, DL_Y + DL_H)],
    dashed=True, label="Install Models",
    label_seg=0, label_side="above"
))

# --- 13. SIEM ↔ Elasticsearch (Data Ingestion) ---
# Straight up from SIEM to data layer bottom (Elasticsearch area)
siem_x = SIEM_X + SIEM_W / 2
dwg.add(elbow_path(
    [(siem_x, SIEM_Y),
     (siem_x, DL_Y + DL_H)],
    bidi=True, dashed=True, label="Data Ingestion",
    label_seg=0, label_side="above"
))

# --- 14. LLM Providers ↔ Backend (Chat Streaming) ---
# Elbow: up from LLM top, left to backend area, up into backend bottom
llm_top_x = LLM_X + 80
chat_route_y = K8S_Y + K8S_H + 8  # just below K8s
dwg.add(elbow_path(
    [(llm_top_x, LLM_Y),
     (llm_top_x, chat_route_y),
     (BE_X + BE_W - 30, chat_route_y),
     (BE_X + BE_W - 30, DL_Y + DL_H)],
    bidi=True, dashed=True, label="Chat Streaming",
    label_seg=1, label_side="below"
))

# --- 15. Security Analysts ↔ Frontend (handled by edge 3 above) ---
# Already done as edge 3


# ═══════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════
LEG_X, LEG_Y = 60, 968
dwg.add(text(LEG_X, LEG_Y, "Legend", size=13, weight="bold",
             fill=C_TITLE, anchor="start"))

legend_items = [
    (C_FRONTEND, C_FRONTEND_BD, "Frontend"),
    (C_BACKEND, C_BACKEND_BD, "Backend"),
    (C_DATA, C_DATA_BD, "Data / Storage"),
    (C_EXEC, C_EXEC_BD, "Execution"),
    ("#e0f7fa", "#00838F", "External"),
]
for i, (fill, stroke, label) in enumerate(legend_items):
    lx = LEG_X + i * 140
    ly = LEG_Y + 18
    dwg.add(solid_box(lx, ly, 16, 16, fill, stroke, rx=3))
    dwg.add(text(lx + 24, ly + 13, label, size=10, fill=C_BODY, anchor="start"))

# Arrow legend
ly2 = LEG_Y + 48
dwg.add(dwg.line(start=(LEG_X, ly2), end=(LEG_X + 40, ly2),
                 stroke=C_ARROW, stroke_width=1.5))
dwg.add(text(LEG_X + 48, ly2 + 4, "Primary data flow",
             size=10, fill=C_BODY, anchor="start"))
dwg.add(dwg.line(start=(LEG_X + 200, ly2), end=(LEG_X + 240, ly2),
                 stroke=C_ARROW_DASH, stroke_width=1.5,
                 stroke_dasharray="6,3"))
dwg.add(text(LEG_X + 248, ly2 + 4, "Secondary / optional",
             size=10, fill=C_BODY, anchor="start"))

# Elbow indicator
dwg.add(dwg.line(start=(LEG_X + 430, ly2), end=(LEG_X + 450, ly2),
                 stroke=C_ARROW, stroke_width=1.5))
dwg.add(dwg.line(start=(LEG_X + 450, ly2), end=(LEG_X + 450, ly2 - 12),
                 stroke=C_ARROW, stroke_width=1.5))
dwg.add(text(LEG_X + 458, ly2 + 4, "Orthogonal routing",
             size=10, fill=C_BODY, anchor="start"))

# Footer
dwg.add(text(W / 2, H - 12,
             "OpenUBA v0.0.2 \u2014 Kubernetes-Native UEBA Platform "
             "\u2014 github.com/GACWR/OpenUBA",
             size=10, fill="#BDBDBD"))


# ─── Save ─────────────────────────────────────────────────────────────
dwg.save()
print(f"Architecture diagram saved to: {OUT}")
print(f"Size: {W}x{H} SVG")
