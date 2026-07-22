#!/usr/bin/env bash
#
# Clean Historical Data — ComfyUI
#
# Usage:
#   ./scripts/clean-history.bash [DAYS] [--dry-run]
#
# Arguments:
#   DAYS      Number of days to retain (default: 7)
#   --dry-run Show what would be deleted without actually deleting
#
# Examples:
#   ./scripts/clean-history.bash              # Delete files older than 7 days
#   ./scripts/clean-history.bash 14           # Delete files older than 14 days
#   ./scripts/clean-history.bash 3 --dry-run  # Preview deletions for 3-day retention
#
set -euo pipefail

PROJECT_ROOT="/Volumes/Kathi/AntiGravity/ComfyUI"
OUTPUT_DIR="${PROJECT_ROOT}/data/output"
TEMP_DIR="${PROJECT_ROOT}/data/temp"
USER_DIR="${PROJECT_ROOT}/data/user"
LOG_FILE="${PROJECT_ROOT}/data/cleanup.log"

# ---- Parse arguments ----
DAYS=${1:-7}
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
    esac
done

# Validate DAYS is a positive integer
if ! [[ "$DAYS" =~ ^[0-9]+$ ]] || [ "$DAYS" -eq 0 ]; then
    echo "ERROR: DAYS must be a positive integer. Got: '$DAYS'"
    echo "Usage: $0 [DAYS] [--dry-run]"
    exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TOTAL_FILES=0
TOTAL_BYTES=0

echo "======================================"
echo " ComfyUI History Cleanup"
echo "======================================"
echo "  Retention: ${DAYS} days"
echo "  Dry run:   ${DRY_RUN}"
echo "  Timestamp: ${TIMESTAMP}"
echo ""

# ---- Function to clean a directory ----
clean_directory() {
    local dir="$1"
    local label="$2"

    if [ ! -d "$dir" ]; then
        echo "[SKIP] ${label}: directory does not exist"
        return
    fi

    echo "[SCAN] ${label}: ${dir}"

    # Find files older than N days
    local count=0
    local bytes=0

    while IFS= read -r -d '' file; do
        local size
        size=$(stat -f%z "$file" 2>/dev/null || echo 0)
        bytes=$((bytes + size))
        count=$((count + 1))

        if [ "$DRY_RUN" = true ]; then
            echo "  [DRY-RUN] Would delete: ${file} ($(numfmt --to=iec $size 2>/dev/null || echo ${size}B))"
        else
            rm -f "$file"
            echo "  [DELETE] ${file} ($(numfmt --to=iec $size 2>/dev/null || echo ${size}B))"
        fi
    done < <(find "$dir" -type f -mtime +"${DAYS}" -print0 2>/dev/null)

    echo "  → ${count} files, $(numfmt --to=iec $bytes 2>/dev/null || echo ${bytes}B)"
    TOTAL_FILES=$((TOTAL_FILES + count))
    TOTAL_BYTES=$((TOTAL_BYTES + bytes))
}

# ---- Clean each directory ----
clean_directory "$OUTPUT_DIR" "Output Images"
echo ""
clean_directory "$TEMP_DIR" "Temp Files"
echo ""
clean_directory "$USER_DIR" "User History"

# ---- Summary ----
echo ""
echo "======================================"
echo " Summary"
echo "======================================"
MODE="DELETED"
if [ "$DRY_RUN" = true ]; then
    MODE="WOULD DELETE"
fi
echo "  ${MODE}: ${TOTAL_FILES} files ($(numfmt --to=iec $TOTAL_BYTES 2>/dev/null || echo ${TOTAL_BYTES}B))"

# ---- Log to file (skip in dry-run) ----
if [ "$DRY_RUN" = false ]; then
    echo "[${TIMESTAMP}] Cleaned ${TOTAL_FILES} files (${TOTAL_BYTES} bytes) | Retention: ${DAYS} days" >> "$LOG_FILE"

    # Log to PostgreSQL if docker is available
    if command -v docker &>/dev/null; then
        cd "${PROJECT_ROOT}"
        docker compose exec -T db psql -U "${POSTGRES_USER:-comfyui}" -d "${POSTGRES_DB:-comfyui}" \
            -c "INSERT INTO cleanup_logs (files_deleted, bytes_freed, retention_days) VALUES (${TOTAL_FILES}, ${TOTAL_BYTES}, ${DAYS});" \
            2>/dev/null || true
    fi
fi

echo ""
echo "Done."
