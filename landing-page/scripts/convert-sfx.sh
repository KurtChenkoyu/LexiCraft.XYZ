#!/bin/bash
# Convert Kenney WAV/OGG files to MP3 and rename to match convention
# Usage: ./convert-sfx.sh <input_directory> <output_directory>
# Example: ./convert-sfx.sh ~/Downloads/kenney-interface-sounds-master/addons/kenney_interface_sounds ./public/audio/fx

INPUT_DIR="${1:-./kenney-interface-sounds}"
OUTPUT_DIR="${2:-./landing-page/public/audio/fx}"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it first:"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
    exit 1
fi

echo "Converting Kenney WAV/OGG files to MP3..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Sound mapping based on advisor's recommendations
# Click: Keep similar (subtle variations)
# Celebrate/Levelup: Make distinct

# Correct sounds (use confirmation sounds - only 4 available, use select for 5th)
echo "Converting correct sounds..."
for i in {1..4}; do
    input_file="$INPUT_DIR/confirmation_$(printf "%03d" $i).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/confirmation_$(printf "%03d" $i).ogg"
    fi
    output_file="$OUTPUT_DIR/correct_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done
# Use select_001 for 5th variant (similar positive sound)
if [ -f "$INPUT_DIR/select_001.wav" ] || [ -f "$INPUT_DIR/select_001.ogg" ]; then
    input_file="$INPUT_DIR/select_001.wav"
    [ ! -f "$input_file" ] && input_file="$INPUT_DIR/select_001.ogg"
    ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$OUTPUT_DIR/correct_005.mp3" 2>/dev/null
    echo "  ✓ $OUTPUT_DIR/correct_005.mp3"
fi

# Wrong sounds (use error sounds)
echo "Converting wrong sounds..."
for i in {1..5}; do
    input_file="$INPUT_DIR/error_$(printf "%03d" $i).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/error_$(printf "%03d" $i).ogg"
    fi
    output_file="$OUTPUT_DIR/wrong_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done

# Click sounds (use click sounds - keep similar)
echo "Converting click sounds..."
for i in {1..5}; do
    input_file="$INPUT_DIR/click_$(printf "%03d" $i).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/click_$(printf "%03d" $i).ogg"
    fi
    output_file="$OUTPUT_DIR/click_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done

# Levelup sounds (use select sounds for variety - make distinct)
echo "Converting levelup sounds..."
for i in {1..5}; do
    # Use select sounds 2-6 for variety (different from correct)
    source_num=$((i + 1))
    input_file="$INPUT_DIR/select_$(printf "%03d" $source_num).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/select_$(printf "%03d" $source_num).ogg"
    fi
    output_file="$OUTPUT_DIR/levelup_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done

# Celebrate sounds (use maximize sounds for variety - make distinct)
echo "Converting celebrate sounds..."
for i in {1..5}; do
    # Use maximize sounds for variety (more dramatic)
    input_file="$INPUT_DIR/maximize_$(printf "%03d" $i).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/maximize_$(printf "%03d" $i).ogg"
    fi
    output_file="$OUTPUT_DIR/celebrate_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done

# Unlock sounds (use glass/pluck sounds for variety)
echo "Converting unlock sounds..."
for i in {1..5}; do
    # Use glass sounds for unlock (magical feel)
    input_file="$INPUT_DIR/glass_$(printf "%03d" $i).wav"
    if [ ! -f "$input_file" ]; then
        input_file="$INPUT_DIR/glass_$(printf "%03d" $i).ogg"
    fi
    output_file="$OUTPUT_DIR/unlock_$(printf "%03d" $i).mp3"
    if [ -f "$input_file" ]; then
        ffmpeg -i "$input_file" -codec:a libmp3lame -qscale:a 2 -y "$output_file" 2>/dev/null
        echo "  ✓ $output_file"
    else
        echo "  ⚠ Missing: $input_file"
    fi
done

echo ""
echo "✅ Conversion complete!"
echo "Files are in: $OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "1. Review the converted files"
echo "2. Adjust mapping if needed (some Kenney packs may have different file names)"
echo "3. Run the Supabase upload script when ready"

