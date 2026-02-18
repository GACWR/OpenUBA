#!/usr/bin/env python3
"""
OpenUBA v2 Model Library & Installation Process Diagram Generator

Generates an SVG diagram showing the model discovery, browsing,
installation, and execution pipeline — matching the architecture
diagram's visual style.

Usage: python3 images/diagram/generate_model_library.py
Output: images/diagram/model-library.svg
"""

import os
import svgwrite

# ─── Canvas ───────────────────────────────────────────────────────────
W, H = 1400, 980
OUT = os.path.join(os.path.dirname(__file__), "model-library.svg")

dwg = svgwrite.Drawing(OUT, size=(W, H), profile="full")
dwg.add(dwg.rect(insert=(0, 0), size=(W, H), fill="white"))

# ─── Style constants ─────────────────────────────────────────────────
FONT = "Helvetica, Arial, sans-serif"
TITLE_SIZE = 16
SUBTITLE_SIZE = 13
BODY_SIZE = 11
SMALL_SIZE = 10

# Colors — reuse from architecture diagram for consistency
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
C_HUB = "#e0f2f1"
C_HUB_BD = "#00897B"
C_INSTALL = "#e3f2fd"
C_INSTALL_BD = "#1565C0"
C_ARROW = "#424242"
C_ARROW_DASH = "#9E9E9E"
C_TITLE = "#212121"
C_BODY = "#424242"
C_MUTED = "#757575"

# Phase label colors
C_PHASE = "#37474F"
C_PHASE_BG = "#ECEFF1"

_marker_id = 0


# ─── Helper functions ────────────────────────────────────────────────

def _next_marker_id():
    global _marker_id
    _marker_id += 1
    return f"ml{_marker_id}"


def _make_markers(color, forward=True, reverse=False):
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
    g = dwg.g()
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
    c = color or (C_ARROW_DASH if dashed else C_ARROW)
    g = dwg.g()
    d = f"M{points[0][0]},{points[0][1]}"
    for px, py in points[1:]:
        d += f" L{px},{py}"
    path_attrs = {"stroke": c, "stroke_width": 1.5, "fill": "none"}
    if dashed:
        path_attrs["stroke_dasharray"] = "6,3"
    path = dwg.path(d=d, **path_attrs)
    fwd, rev = _make_markers(c, forward=True, reverse=bidi)
    path["marker-end"] = fwd.get_funciri()
    if bidi and rev:
        path["marker-start"] = rev.get_funciri()
    g.add(path)
    if label:
        if label_seg is None:
            label_seg = len(points) // 2 - 1
        label_seg = max(0, min(label_seg, len(points) - 2))
        p1 = points[label_seg]
        p2 = points[label_seg + 1]
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        if p1[1] == p2[1]:
            offset = -10 if label_side == "above" else 14
            my += offset
        else:
            offset = -8 if label_side == "above" else 8
            mx += offset
        g.add(label_with_bg(mx, my, label))
    return g


def component_box(x, y, w, h, label, sublabel=None, fill="#ffffff", stroke="#bdbdbd"):
    g = dwg.g()
    g.add(solid_box(x, y, w, h, fill, stroke))
    g.add(text(x + w / 2, y + h / 2 + 4, label, size=BODY_SIZE, weight="bold", fill=C_TITLE))
    if sublabel:
        g.add(text(x + w / 2, y + h / 2 + 17, sublabel, size=SMALL_SIZE, fill=C_MUTED))
    return g


def phase_label(x, y, number, label):
    """Draw a numbered phase label with pill background."""
    g = dwg.g()
    # Number pill
    g.add(dwg.circle(center=(x, y), r=14, fill=C_PHASE))
    g.add(text(x, y + 5, str(number), size=14, weight="bold", fill="white"))
    # Label
    g.add(text(x + 24, y + 5, label, size=14, weight="bold",
               fill=C_PHASE, anchor="start"))
    return g


def step_box(x, y, w, h, label, sublabel=None, fill="#ffffff", stroke="#bdbdbd",
             label_color=C_TITLE):
    g = dwg.g()
    g.add(solid_box(x, y, w, h, fill, stroke))
    ly = y + h / 2 + 4 if not sublabel else y + h / 2 - 2
    g.add(text(x + w / 2, ly, label, size=BODY_SIZE, weight="bold", fill=label_color))
    if sublabel:
        g.add(text(x + w / 2, ly + 15, sublabel, size=SMALL_SIZE, fill=C_MUTED))
    return g


# ─── Main title ──────────────────────────────────────────────────────
dwg.add(text(W / 2, 30, "OpenUBA v0.0.2 \u2014 Model Library & Installation Process",
             size=22, weight="bold", fill="#1a1a1a"))
dwg.add(text(W / 2, 48, "Discovery \u2192 Browsing \u2192 Installation \u2192 Execution",
             size=12, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: MODEL SOURCES
# ═══════════════════════════════════════════════════════════════════════
P1_Y = 70
dwg.add(phase_label(80, P1_Y + 15, 1, "DISCOVER"))

SRC_Y = P1_Y + 35
SRC_H = 130

# OpenUBA Hub
HUB_X, HUB_W = 60, 400
dwg.add(dashed_box(HUB_X, SRC_Y, HUB_W, SRC_H, C_HUB, C_HUB_BD,
                   "OpenUBA Model Hub"))
dwg.add(text(HUB_X + HUB_W / 2, SRC_Y + 46, "openuba.org/registry/models.json",
             size=11, weight="bold", fill=C_HUB_BD))
dwg.add(text(HUB_X + HUB_W / 2, SRC_Y + 64, "Static JSON catalog \u2014 7 community models",
             size=10, fill=C_MUTED))

# Model cards inside hub
hub_models = ["model_sklearn", "model_pytorch", "model_tensorflow",
              "model_keras", "model_networkx", "basic_model"]
for i, m in enumerate(hub_models):
    col = i % 3
    row = i // 3
    bx = HUB_X + 20 + col * 125
    by = SRC_Y + 78 + row * 26
    dwg.add(solid_box(bx, by, 118, 22, "#ffffff", C_HUB_BD, rx=4))
    dwg.add(text(bx + 59, by + 15, m, size=9, fill=C_HUB_BD))

# GitHub Repository
GH_X, GH_W = 490, 400
dwg.add(dashed_box(GH_X, SRC_Y, GH_W, SRC_H, C_EXTERNAL, "#333333",
                   "GitHub Repository"))
dwg.add(text(GH_X + GH_W / 2, SRC_Y + 46, "GACWR/openuba-model-hub",
             size=11, weight="bold", fill="#333333"))
dwg.add(text(GH_X + GH_W / 2, SRC_Y + 64, "Raw file delivery via GitHub CDN",
             size=10, fill=C_MUTED))

gh_files = ["MODEL.py", "model.yaml", "__init__.py"]
for i, f in enumerate(gh_files):
    bx = GH_X + 40 + i * 115
    by = SRC_Y + 80
    dwg.add(solid_box(bx, by, 105, 28, "#ffffff", "#333333", rx=4))
    dwg.add(text(bx + 52, by + 18, f, size=10, weight="bold", fill="#333333"))

# Local Filesystem
LFS_X, LFS_W = 920, 420
dwg.add(dashed_box(LFS_X, SRC_Y, LFS_W, SRC_H, C_EXTERNAL, C_EXTERNAL_BD,
                   "Other Registries"))
dwg.add(text(LFS_X + LFS_W / 2, SRC_Y + 46, "Pluggable Adapter Pattern",
             size=11, weight="bold", fill=C_EXTERNAL_BD))

other_regs = [
    ("Local Filesystem", "core/model_library/"),
    ("GitHub Repos", "Any public repo"),
    ("HuggingFace", "Model hub API"),
    ("Custom", "Your registry"),
]
for i, (name, sub) in enumerate(other_regs):
    col = i % 2
    row = i // 2
    bx = LFS_X + 20 + col * 200
    by = SRC_Y + 60 + row * 36
    dwg.add(solid_box(bx, by, 190, 30, "#ffffff", C_EXTERNAL_BD, rx=4))
    dwg.add(text(bx + 95, by + 13, name, size=10, weight="bold", fill=C_BODY))
    dwg.add(text(bx + 95, by + 25, sub, size=8, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: BROWSE & SEARCH (Frontend + Backend Registry)
# ═══════════════════════════════════════════════════════════════════════
P2_Y = SRC_Y + SRC_H + 30
dwg.add(phase_label(80, P2_Y + 15, 2, "BROWSE"))

BROWSE_Y = P2_Y + 35
BROWSE_H = 160

# Registry Service (Backend)
REG_X, REG_W = 60, 440
dwg.add(dashed_box(REG_X, BROWSE_Y, REG_W, BROWSE_H, C_BACKEND, C_BACKEND_BD,
                   "Registry Service (Backend)"))

dwg.add(text(REG_X + REG_W / 2, BROWSE_Y + 46, "RegistryService \u2192 Adapters",
             size=11, weight="bold", fill="#2E7D32"))

# Adapter boxes
adapters = [
    ("Hub Adapter", "fetches catalog JSON", C_HUB, C_HUB_BD),
    ("GitHub Adapter", "clones model repos", C_EXTERNAL, "#333333"),
    ("Local FS Adapter", "scans model_library/", C_EXTERNAL, C_EXTERNAL_BD),
]
for i, (name, desc, fill, stroke) in enumerate(adapters):
    bx = REG_X + 15 + i * 140
    by = BROWSE_Y + 62
    dwg.add(solid_box(bx, by, 132, 42, fill, stroke, rx=4))
    dwg.add(text(bx + 66, by + 16, name, size=10, weight="bold", fill=stroke))
    dwg.add(text(bx + 66, by + 30, desc, size=8, fill=C_MUTED))

# Cache info
dwg.add(solid_box(REG_X + 15, BROWSE_Y + 115, 200, 28, "#ffffff", C_BACKEND_BD, rx=4))
dwg.add(text(REG_X + 115, BROWSE_Y + 133, "Cached catalog (5-min TTL)",
             size=10, fill="#2E7D32"))

# Dedup info
dwg.add(solid_box(REG_X + 225, BROWSE_Y + 115, 200, 28, "#ffffff", C_BACKEND_BD, rx=4))
dwg.add(text(REG_X + 325, BROWSE_Y + 133, "Dedup + installed status",
             size=10, fill="#2E7D32"))

# Frontend Library Tab
FE_X, FE_W = 530, 810
dwg.add(dashed_box(FE_X, BROWSE_Y, FE_W, BROWSE_H, C_FRONTEND, C_FRONTEND_BD,
                   "Frontend \u2014 Model Library Tab"))

# UI flow steps
ui_steps = [
    ("Auto-Load", "GET /api/v1/models/search\n?registry_type=code"),
    ("Search & Filter", "Client-side instant\nfiltering by name/tag"),
    ("Model Table", "Name, framework, version\ninstall status badges"),
    ("Detail Modal", "Overview + source code\ntabs, parameters, tags"),
    ("Install Button", "Progress spinner\nsuccess toast"),
]
for i, (label, desc) in enumerate(ui_steps):
    bx = FE_X + 15 + i * 158
    by = BROWSE_Y + 42
    bw = 148
    bh = 58
    dwg.add(solid_box(bx, by, bw, bh, "#ffffff", C_FRONTEND_BD, rx=4))
    dwg.add(text(bx + bw / 2, by + 18, label, size=10, weight="bold", fill=C_FRONTEND_BD))
    # Split description lines
    lines = desc.split("\n")
    for j, line in enumerate(lines):
        dwg.add(text(bx + bw / 2, by + 32 + j * 12, line, size=8, fill=C_MUTED))

# Arrow flow between UI steps
for i in range(len(ui_steps) - 1):
    x1 = FE_X + 15 + i * 158 + 148
    x2 = FE_X + 15 + (i + 1) * 158
    y_mid = BROWSE_Y + 71
    dwg.add(elbow_path([(x1, y_mid), (x2, y_mid)],
                       color=C_FRONTEND_BD))

# Code fetch note
dwg.add(solid_box(FE_X + 15, BROWSE_Y + 112, 380, 30, "#ffffff", C_FRONTEND_BD, rx=4))
dwg.add(text(FE_X + 205, BROWSE_Y + 131, "Code preview fetches MODEL.py directly from GitHub raw URLs",
             size=9, fill=C_FRONTEND_BD))

dwg.add(solid_box(FE_X + 410, BROWSE_Y + 112, 385, 30, "#ffffff", C_FRONTEND_BD, rx=4))
dwg.add(text(FE_X + 602, BROWSE_Y + 131,
             "raw.githubusercontent.com/GACWR/openuba-model-hub/master/{path}/MODEL.py",
             size=8, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: INSTALLATION
# ═══════════════════════════════════════════════════════════════════════
P3_Y = BROWSE_Y + BROWSE_H + 30
dwg.add(phase_label(80, P3_Y + 15, 3, "INSTALL"))

INST_Y = P3_Y + 35
INST_H = 180

# Installation Pipeline
INST_X, INST_W = 60, 860
dwg.add(dashed_box(INST_X, INST_Y, INST_W, INST_H, C_INSTALL, C_INSTALL_BD,
                   "Model Installation Pipeline"))

# Step boxes in sequence
inst_steps = [
    ("Register in DB", "POST /api/v1/models\nCreate model record"),
    ("Download Files", "Hub adapter fetches\nMODEL.py, model.yaml"),
    ("Verify Integrity", "Compute file hashes\nCompare with manifest"),
    ("Write to Disk", "model_library/<slug>/\n<version>/MODEL.py"),
    ("Mark Installed", "model_versions.status\n= 'installed'"),
]
for i, (label, desc) in enumerate(inst_steps):
    bx = INST_X + 18 + i * 168
    by = INST_Y + 40
    bw = 155
    bh = 62
    dwg.add(solid_box(bx, by, bw, bh, "#ffffff", C_INSTALL_BD, rx=5))
    dwg.add(text(bx + bw / 2, by + 18, label, size=11, weight="bold", fill=C_INSTALL_BD))
    lines = desc.split("\n")
    for j, line in enumerate(lines):
        dwg.add(text(bx + bw / 2, by + 34 + j * 13, line, size=9, fill=C_MUTED))
    # Step number circle
    dwg.add(dwg.circle(center=(bx + 12, by + 8), r=9,
                       fill=C_INSTALL_BD))
    dwg.add(text(bx + 12, by + 12, f"{i + 1}", size=9, weight="bold", fill="white"))

# Arrows between install steps
for i in range(len(inst_steps) - 1):
    x1 = INST_X + 18 + i * 168 + 155
    x2 = INST_X + 18 + (i + 1) * 168
    step_y = INST_Y + 71
    dwg.add(elbow_path([(x1, step_y), (x2, step_y)],
                       color=C_INSTALL_BD))

# API endpoint note
dwg.add(solid_box(INST_X + 18, INST_Y + 115, 410, 45, "#ffffff", C_INSTALL_BD, rx=4))
dwg.add(text(INST_X + 223, INST_Y + 133, "POST /api/v1/models/{id}/install",
             size=11, weight="bold", fill=C_INSTALL_BD))
dwg.add(text(INST_X + 223, INST_Y + 149,
             "Triggers hub adapter download \u2192 writes files \u2192 updates DB status",
             size=9, fill=C_MUTED))

# Hash verification note
dwg.add(solid_box(INST_X + 440, INST_Y + 115, 400, 45, "#ffffff", C_INSTALL_BD, rx=4))
dwg.add(text(INST_X + 640, INST_Y + 133, "Cryptographic Verification",
             size=11, weight="bold", fill=C_INSTALL_BD))
dwg.add(text(INST_X + 640, INST_Y + 149,
             "SHA-256 hash check at install + before every execution",
             size=9, fill=C_MUTED))

# Storage targets (right side)
STOR_X, STOR_W = 950, 390
dwg.add(dashed_box(STOR_X, INST_Y, STOR_W, INST_H, C_DATA, C_DATA_BD,
                   "Storage"))

# Model Library on disk
dwg.add(solid_box(STOR_X + 15, INST_Y + 38, 170, 58, "#ffffff", C_DATA_BD, rx=4))
dwg.add(text(STOR_X + 100, INST_Y + 56, "Model Library", size=11, weight="bold",
             fill="#E65100"))
dwg.add(text(STOR_X + 100, INST_Y + 70, "core/model_library/", size=9, fill=C_MUTED))
dwg.add(text(STOR_X + 100, INST_Y + 83, "<slug>/<version>/", size=9, fill=C_MUTED))

# PostgreSQL
dwg.add(solid_box(STOR_X + 200, INST_Y + 38, 170, 58, "#ffffff", C_DATA_BD, rx=4))
dwg.add(text(STOR_X + 285, INST_Y + 56, "PostgreSQL", size=11, weight="bold",
             fill="#E65100"))
dwg.add(text(STOR_X + 285, INST_Y + 70, "models table", size=9, fill=C_MUTED))
dwg.add(text(STOR_X + 285, INST_Y + 83, "model_versions table", size=9, fill=C_MUTED))

# Artifact Storage
dwg.add(solid_box(STOR_X + 15, INST_Y + 108, 170, 55, "#ffffff", C_DATA_BD, rx=4))
dwg.add(text(STOR_X + 100, INST_Y + 126, "Artifact Storage", size=11, weight="bold",
             fill="#E65100"))
dwg.add(text(STOR_X + 100, INST_Y + 140, "saved_models/<slug>/", size=9, fill=C_MUTED))
dwg.add(text(STOR_X + 100, INST_Y + 152, "<version>/<run_id>/", size=9, fill=C_MUTED))

# Persistent Volumes
dwg.add(solid_box(STOR_X + 200, INST_Y + 108, 170, 55, "#ffffff", C_DATA_BD, rx=4))
dwg.add(text(STOR_X + 285, INST_Y + 126, "Persistent Volumes", size=11, weight="bold",
             fill="#E65100"))
pvcs = ["source-code-pvc", "saved-models-pvc", "system-storage-pvc"]
for i, pvc in enumerate(pvcs):
    dwg.add(text(STOR_X + 285, INST_Y + 140 + i * 11, pvc, size=8, fill=C_MUTED))


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: EXECUTION
# ═══════════════════════════════════════════════════════════════════════
P4_Y = INST_Y + INST_H + 30
dwg.add(phase_label(80, P4_Y + 15, 4, "EXECUTE"))

EXEC_Y = P4_Y + 35
EXEC_H = 170

dwg.add(dashed_box(60, EXEC_Y, 1280, EXEC_H, C_EXEC, C_EXEC_BD,
                   "Model Execution Pipeline"))

# Execution steps
exec_steps = [
    ("API Request", "POST /models/{id}/\ntrain or infer",
     "#ffffff", C_BACKEND_BD, "#2E7D32"),
    ("Orchestrator", "Creates CRD spec\nbackground thread",
     "#ffffff", C_BACKEND_BD, "#2E7D32"),
    ("Operator", "Watches CRDs\ncreates K8s Job",
     "#fce4ec", "#c62828", "#c62828"),
    ("K8s Job", "Ephemeral pod\nframework-specific",
     C_EXEC, C_EXEC_BD, "#6A1B9A"),
    ("Model Runner", "Loads code + data\ntrains or infers",
     C_EXEC, C_EXEC_BD, "#6A1B9A"),
    ("Results", "Anomalies \u2192 DB\nRisk scores \u2192 ES",
     C_DATA, C_DATA_BD, "#E65100"),
]
for i, (label, desc, fill, stroke, label_color) in enumerate(exec_steps):
    bx = 80 + i * 207
    by = EXEC_Y + 40
    bw = 192
    bh = 62
    dwg.add(solid_box(bx, by, bw, bh, fill, stroke, rx=5))
    dwg.add(text(bx + bw / 2, by + 18, label, size=11, weight="bold",
                 fill=label_color))
    lines = desc.split("\n")
    for j, line in enumerate(lines):
        dwg.add(text(bx + bw / 2, by + 34 + j * 13, line, size=9, fill=C_MUTED))

# Arrows between exec steps
for i in range(len(exec_steps) - 1):
    x1 = 80 + i * 207 + 192
    x2 = 80 + (i + 1) * 207
    exec_mid_y = EXEC_Y + 71
    dwg.add(elbow_path([(x1, exec_mid_y), (x2, exec_mid_y)],
                       color=C_EXEC_BD))

# Runner images
dwg.add(text(W / 2, EXEC_Y + 120, "Framework-Specific Runner Images",
             size=12, weight="bold", fill="#6A1B9A"))
runtimes = ["model-runner:sklearn", "model-runner:pytorch",
            "model-runner:tensorflow", "model-runner:networkx"]
for i, rt in enumerate(runtimes):
    bx = 180 + i * 270
    by = EXEC_Y + 132
    dwg.add(solid_box(bx, by, 245, 22, "#ffffff", C_EXEC_BD, rx=4))
    dwg.add(text(bx + 122, by + 15, rt, size=10, weight="bold", fill="#6A1B9A"))


# ═══════════════════════════════════════════════════════════════════════
# CONNECTING ARROWS BETWEEN PHASES
# ═══════════════════════════════════════════════════════════════════════

# 1. Hub → Registry Service (catalog fetch)
dwg.add(elbow_path(
    [(HUB_X + HUB_W / 2, SRC_Y + SRC_H),
     (HUB_X + HUB_W / 2, BROWSE_Y + 18),
     (REG_X + REG_W / 2, BROWSE_Y + 18),
     (REG_X + REG_W / 2, BROWSE_Y)],
    label="catalog JSON", label_seg=1, label_side="above",
    color=C_HUB_BD
))

# 2. GitHub → Frontend (raw code fetch for detail modal)
dwg.add(elbow_path(
    [(GH_X + GH_W / 2, SRC_Y + SRC_H),
     (GH_X + GH_W / 2, BROWSE_Y + 18),
     (FE_X + 620, BROWSE_Y + 18),
     (FE_X + 620, BROWSE_Y)],
    dashed=True, label="MODEL.py (raw)", label_seg=1, label_side="above",
    color="#333333"
))

# 3. Other Registries → Registry Service (adapter queries)
dwg.add(elbow_path(
    [(LFS_X + LFS_W / 2, SRC_Y + SRC_H),
     (LFS_X + LFS_W / 2, BROWSE_Y + 18),
     (REG_X + REG_W - 30, BROWSE_Y + 18),
     (REG_X + REG_W - 30, BROWSE_Y)],
    dashed=True, label="adapter queries", label_seg=1, label_side="above"
))

# 4. Registry Service → Frontend (search results)
dwg.add(elbow_path(
    [(REG_X + REG_W, BROWSE_Y + 80),
     (FE_X, BROWSE_Y + 80)],
    bidi=True, label="search results + status",
    label_seg=0, label_side="above"
))

# 5. Frontend → Install Pipeline (install request)
fe_install_x = FE_X + 660
dwg.add(elbow_path(
    [(fe_install_x, BROWSE_Y + BROWSE_H),
     (fe_install_x, INST_Y + 18),
     (INST_X + INST_W / 2, INST_Y + 18),
     (INST_X + INST_W / 2, INST_Y)],
    label="POST /install", label_seg=1, label_side="above",
    color=C_INSTALL_BD
))

# 6. Install Pipeline → Storage (write files + DB records)
dwg.add(elbow_path(
    [(INST_X + INST_W, INST_Y + 80),
     (STOR_X, INST_Y + 80)],
    label="write files + records",
    label_seg=0, label_side="above",
    color=C_DATA_BD
))

# 7. Storage → Execution (load model code + artifacts)
stor_bottom_x = STOR_X + STOR_W / 2
dwg.add(elbow_path(
    [(stor_bottom_x, INST_Y + INST_H),
     (stor_bottom_x, EXEC_Y + 18),
     (W / 2, EXEC_Y + 18),
     (W / 2, EXEC_Y)],
    dashed=True, label="mount PVCs", label_seg=1, label_side="above",
    color=C_EXEC_BD
))

# 8. Install Pipeline → Execution (model is now executable)
dwg.add(elbow_path(
    [(INST_X + 200, INST_Y + INST_H),
     (INST_X + 200, EXEC_Y)],
    dashed=True, label="model ready",
    label_seg=0, label_side="above",
    color=C_BACKEND_BD
))


# ═══════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════
LEG_X, LEG_Y = 60, H - 65
dwg.add(text(LEG_X, LEG_Y, "Legend", size=13, weight="bold",
             fill=C_TITLE, anchor="start"))

legend_items = [
    (C_HUB, C_HUB_BD, "Model Hub"),
    (C_FRONTEND, C_FRONTEND_BD, "Frontend"),
    (C_BACKEND, C_BACKEND_BD, "Backend"),
    (C_INSTALL, C_INSTALL_BD, "Installation"),
    (C_DATA, C_DATA_BD, "Storage"),
    (C_EXEC, C_EXEC_BD, "Execution"),
    (C_EXTERNAL, C_EXTERNAL_BD, "External"),
]
for i, (fill, stroke, label) in enumerate(legend_items):
    lx = LEG_X + i * 145
    ly = LEG_Y + 18
    dwg.add(solid_box(lx, ly, 16, 16, fill, stroke, rx=3))
    dwg.add(text(lx + 24, ly + 13, label, size=10, fill=C_BODY, anchor="start"))

# Arrow legend
ly2 = LEG_Y + 48
dwg.add(dwg.line(start=(LEG_X, ly2), end=(LEG_X + 40, ly2),
                 stroke=C_ARROW, stroke_width=1.5))
dwg.add(text(LEG_X + 48, ly2 + 4, "Primary flow",
             size=10, fill=C_BODY, anchor="start"))
dwg.add(dwg.line(start=(LEG_X + 180, ly2), end=(LEG_X + 220, ly2),
                 stroke=C_ARROW_DASH, stroke_width=1.5,
                 stroke_dasharray="6,3"))
dwg.add(text(LEG_X + 228, ly2 + 4, "Secondary / optional",
             size=10, fill=C_BODY, anchor="start"))

# Footer
dwg.add(text(W / 2, H - 8,
             "OpenUBA v0.0.2 \u2014 Model Library & Installation "
             "\u2014 github.com/GACWR/OpenUBA",
             size=10, fill="#BDBDBD"))


# ─── Save ─────────────────────────────────────────────────────────────
dwg.save()
print(f"Model library diagram saved to: {OUT}")
print(f"Size: {W}x{H} SVG")
