#!/usr/bin/env python3
"""
Final Dashboard Assembly
--------------------------
Runs the data builder, then combines template.html + dashboard.js +
dashboard_data.json + the author photo into ONE self-contained
dashboard/dist/index.html (and a docs/index.html copy for GitHub Pages).
"""
import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..")
DIST = os.path.join(HERE, "dist")
DOCS = os.path.join(BASE, "docs")
os.makedirs(DIST, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

# 1. Build the data payload
rc = subprocess.call([sys.executable, os.path.join(HERE, "build_dashboard_data.py")])
if rc != 0:
    sys.exit(rc)

with open(os.path.join(HERE, "template.html")) as f:
    template = f.read()
with open(os.path.join(HERE, "dashboard.js")) as f:
    dashboard_js = f.read()
with open(os.path.join(HERE, "chart.umd.js")) as f:
    chartjs = f.read()
with open(os.path.join(DIST, "dashboard_data.json")) as f:
    dashboard_data = f.read()

photo_path = os.path.join(HERE, "assets", "milad-shabani.jpg")
if os.path.exists(photo_path):
    with open(photo_path, "rb") as f:
        photo_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
else:
    photo_b64 = ("data:image/svg+xml;base64," + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
        b'<rect width="64" height="64" rx="32" fill="#0B2545"/>'
        b'<text x="32" y="40" font-size="22" fill="#fff" text-anchor="middle" font-family="Arial">MS</text></svg>'
    ).decode())

dashboard_js_inlined = dashboard_js.replace("__AUTHOR_PHOTO__", photo_b64)

html = template.replace("__DASHBOARD_DATA__", dashboard_data)
html = html.replace("__CHARTJS__", chartjs)
html = html.replace("__DASHBOARD_JS__", dashboard_js_inlined)

out_path = os.path.join(DIST, "index.html")
with open(out_path, "w") as f:
    f.write(html)
with open(os.path.join(DOCS, "index.html"), "w") as f:
    f.write(html)

print(f"Dashboard written: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")
print(f"GitHub Pages copy: {os.path.join(DOCS, 'index.html')}")
