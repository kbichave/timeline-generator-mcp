#!/bin/bash
# Generate all example timelines
# Usage: ./generate_examples.sh

set -e

echo "Timeline Generator - Generating Examples"
echo "============================================"

# Ensure output directory exists
mkdir -p output

# Static PNG examples
echo ""
echo "[PNG] Generating static images..."

timeline-gen generate examples/project_timeline.yaml -o output/project_timeline.png
echo "  [OK] project_timeline.png"

timeline-gen generate examples/dense_timeline.yaml -o output/dense_timeline.png
echo "  [OK] dense_timeline.png"

timeline-gen generate examples/company_history.yaml -o output/company_history.png
echo "  [OK] company_history.png"

timeline-gen generate examples/sprint_gantt.yaml -o output/sprint_gantt.png
echo "  [OK] sprint_gantt.png"

timeline-gen generate examples/product_roadmap.yaml -o output/product_roadmap.png
echo "  [OK] product_roadmap.png"

timeline-gen generate examples/personal_goals.yaml -o output/personal_goals.png
echo "  [OK] personal_goals.png"

# Animated GIF examples
echo ""
echo "[GIF] Generating animated images..."

timeline-gen generate examples/project_timeline.yaml -o output/project_timeline.gif -f gif --fps 20 -d 4
echo "  [OK] project_timeline.gif"

timeline-gen generate examples/company_history.yaml -o output/company_history.gif -f gif --fps 15 -d 6
echo "  [OK] company_history.gif"

timeline-gen generate examples/sprint_gantt.yaml -o output/sprint_gantt.gif -f gif --fps 20 -d 4
echo "  [OK] sprint_gantt.gif"

timeline-gen generate examples/personal_goals.yaml -o output/personal_goals.gif -f gif --fps 20 -d 5
echo "  [OK] personal_goals.gif"

# Quick command examples
echo ""
echo "[QUICK] Generating quick examples..."

timeline-gen quick "2024-01-01:Project Start" "2024-03-15:Phase 1" "2024-06-01:MVP Launch" "2024-09-01:Scale" "2024-12-01:v2.0 Release" \
  --style horizontal --theme dark -o output/quick_dark.png
echo "  [OK] quick_dark.png"

timeline-gen quick "2024-01-01:Founded" "2024-06-01:Seed Round" "2024-12-01:Product Launch" \
  --style vertical --theme corporate -o output/quick_vertical.png
echo "  [OK] quick_vertical.png"

# Transparent background example
echo ""
echo "[TRANSPARENT] Generating transparent example..."

timeline-gen generate examples/project_timeline.yaml -o output/project_timeline_transparent.png --transparent
echo "  [OK] project_timeline_transparent.png"

# TOON format examples (30-60% fewer tokens than YAML)
echo ""
echo "[TOON] Generating from TOON format examples..."

timeline-gen generate examples/project_timeline.toon -o output/project_timeline_toon.png
echo "  [OK] project_timeline_toon.png (from TOON)"

timeline-gen generate examples/company_history.toon -o output/company_history_toon.png
echo "  [OK] company_history_toon.png (from TOON)"

timeline-gen generate examples/sprint_gantt.toon -o output/sprint_gantt_toon.png
echo "  [OK] sprint_gantt_toon.png (from TOON)"

timeline-gen generate examples/project_timeline.toon -o output/project_timeline_toon.gif -f gif --fps 20 -d 4
echo "  [OK] project_timeline_toon.gif (from TOON)"

echo ""
echo "============================================"
echo "[DONE] All examples generated in output/"
echo ""
ls -la output/
