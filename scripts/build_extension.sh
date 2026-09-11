#!/usr/bin/env bash
set -e

# Define PROJECT_ROOT as the script's parent's parent directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="dist/ai_writer_assistant.oxt"

# Create dist/ directory
mkdir -p "$PROJECT_ROOT/dist"

# Remove old .oxt if exists
if [ -f "$PROJECT_ROOT/$OUTPUT" ]; then
    rm -f "$PROJECT_ROOT/$OUTPUT"
fi

# Create a temporary build directory
BUILD_DIR="$(mktemp -d)"

# Ensure cleanup on exit
cleanup() {
    rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

# Copy extension/Addons.xcu, extension/description.xml, extension/META-INF/ to a temp build dir
cp "$PROJECT_ROOT/extension/Addons.xcu" "$BUILD_DIR/"
cp "$PROJECT_ROOT/extension/description.xml" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/extension/META-INF" "$BUILD_DIR/"

# Copy extension/python/ to the build dir
cp -r "$PROJECT_ROOT/extension/python" "$BUILD_DIR/"

# Copy config/ and src/ (excluding __pycache__) to the build dir
mkdir -p "$BUILD_DIR/config" "$BUILD_DIR/src"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '__pycache__' --exclude '*.pyc' "$PROJECT_ROOT/config/" "$BUILD_DIR/config/"
    rsync -a --exclude '__pycache__' --exclude '*.pyc' "$PROJECT_ROOT/src/" "$BUILD_DIR/src/"
else
    cp -r "$PROJECT_ROOT/config" "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/"
    find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} +
    find "$BUILD_DIR" -type f -name "*.pyc" -delete
fi

# Copy LICENSE.txt if present
if [ -f "$PROJECT_ROOT/LICENSE.txt" ]; then
    cp "$PROJECT_ROOT/LICENSE.txt" "$BUILD_DIR/"
fi

# cd into the build dir and zip everything into the .oxt file
cd "$BUILD_DIR"
zip -q -r "ai_writer_assistant.oxt" .

# Move the .oxt to $PROJECT_ROOT/dist/
mv "ai_writer_assistant.oxt" "$PROJECT_ROOT/dist/"

# Clean up temp dir
cd "$PROJECT_ROOT"
rm -rf "$BUILD_DIR"
trap - EXIT

# Print success message with file size
FILE_SIZE=$(du -h "$PROJECT_ROOT/$OUTPUT" | cut -f1)
echo "Extension successfully built: $OUTPUT ($FILE_SIZE)"
