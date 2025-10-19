#!/bin/bash
# Script to create a Kodi addon ZIP file

ADDON_NAME="service.siri.remote"

# Get version from command line argument or use default
if [ -n "$1" ]; then
    VERSION="$1"
else
    # Default version if not specified
    VERSION="1.0.0"
fi

ZIP_NAME="${ADDON_NAME}-${VERSION}.zip"

echo "Creating Kodi addon ZIP: ${ZIP_NAME}"
echo "Version: ${VERSION}"
echo ""

# Install dependencies first
echo "Installing dependencies..."
./install_dependencies.sh
if [ $? -ne 0 ]; then
    echo "❌ Error installing dependencies"
    exit 1
fi
echo ""

# Remove old zip if it exists
if [ -f "${ZIP_NAME}" ]; then
    echo "Removing old ${ZIP_NAME}..."
    rm "${ZIP_NAME}"
fi

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
ADDON_DIR="${TEMP_DIR}/${ADDON_NAME}"

echo "Preparing addon structure..."
mkdir -p "${ADDON_DIR}"

# Copy all addon files to the temp directory
cp -r addon.xml service.py remote resources lib "${ADDON_DIR}/"
# Copy settings.xml to both root and resources for compatibility
cp settings.xml "${ADDON_DIR}/"
cp settings.xml "${ADDON_DIR}/resources/"

# Remove __pycache__ directories
find "${ADDON_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${ADDON_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${ADDON_DIR}" -type f -name "*.pyo" -delete 2>/dev/null || true

# Create the zip file from the temp directory
echo "Packaging addon files..."
cd "${TEMP_DIR}"
zip -r -q "${ZIP_NAME}" "${ADDON_NAME}/"

# Move the zip to the original directory
mv "${ZIP_NAME}" "${OLDPWD}/"
cd "${OLDPWD}"

# Clean up temp directory
rm -rf "${TEMP_DIR}"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Created: ${ZIP_NAME}"
    echo ""
    echo "To install in Kodi:"
    echo "  1. Go to Settings → Add-ons → Install from zip file"
    echo "  2. Select ${ZIP_NAME}"
    echo "  3. Configure the addon with your remote's MAC address"
    echo ""
    echo "Usage: $0 [version]"
    echo "  Example: $0 1.0.1"
    echo ""
else
    echo ""
    echo "❌ Error creating ZIP file"
    exit 1
fi

