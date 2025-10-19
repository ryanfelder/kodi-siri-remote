#!/bin/bash
# Install Python dependencies for Siri Remote Kodi Addon
# This script installs all required packages into lib/ for Kodi's sandboxed Python environment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# List of required dependencies
# Only dbus-fast is needed - we communicate directly with BlueZ via D-Bus
DEPENDENCIES=(
    "dbus-fast"
)

echo "=========================================="
echo "Installing Siri Remote Addon Dependencies"
echo "=========================================="
echo ""
echo "Target directory: $LIB_DIR"
echo ""

# Clean up completely for consistency
echo "Cleaning up old installations..."
if [ -d "$LIB_DIR" ]; then
    rm -rf "$LIB_DIR"
    echo "✓ Removed old lib directory"
fi
mkdir -p "$LIB_DIR"
echo "✓ Created fresh lib directory"

echo ""
echo "Installing dependencies..."
echo ""

# Install each dependency
for dep in "${DEPENDENCIES[@]}"; do
    echo "Installing $dep..."
    python3 -m pip install \
        --target="$LIB_DIR" \
        --upgrade \
        --no-warn-script-location \
        "$dep"
done

echo ""
echo "Cleaning up platform-specific packages..."

# Remove Windows-specific packages
find "$LIB_DIR" -type d -name "*winrt*" -exec rm -rf {} + 2>/dev/null || true
find "$LIB_DIR" -type d -name "*win32*" -exec rm -rf {} + 2>/dev/null || true

# Remove macOS-specific packages  
find "$LIB_DIR" -type d -name "*pyobjc*" -exec rm -rf {} + 2>/dev/null || true
find "$LIB_DIR" -type d -name "*corebluetooth*" -exec rm -rf {} + 2>/dev/null || true

# Remove Android-specific packages
find "$LIB_DIR" -type d -name "*p4android*" -exec rm -rf {} + 2>/dev/null || true

# Clean up compiled Python files
find "$LIB_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$LIB_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$LIB_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove any leftover bin/scripts directories
rm -rf "$LIB_DIR/bin" 2>/dev/null || true

echo "✓ Cleaned up platform-specific packages"

echo ""
echo "=========================================="
echo "Installed packages:"
echo "=========================================="
ls -1 "$LIB_DIR" | grep -vE "^(__pycache__|bin)$"

echo ""
echo "=========================================="
echo "Verifying imports..."
echo "=========================================="

# Verify dbus_fast can be imported
PYTHONPATH="$LIB_DIR:$PYTHONPATH" python3 << 'EOF'
import sys

try:
    import dbus_fast
    import importlib.metadata
    version = importlib.metadata.version('dbus-fast')
    print(f'✓ dbus_fast {version}')
except ImportError as e:
    print(f'✗ dbus_fast: {e}')
    sys.exit(1)
EOF

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "All dependencies installed for Linux-only Kodi addon."
echo "The lib/ directory is ready to be packaged with the addon."
echo ""
