import string
from typing import List, Tuple, Dict, Optional
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
import logging

TARGET_SIZE = 32000
PADDING = 256
SIMPLIFY_TOLERANCE = 0.005

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Type aliases
Contour = List[Tuple[str, Tuple]]
Point = Tuple[float, float]

# Hardcoded input and output file paths
INPUT_FONT = "jbmono_regular.ttf"
OUTPUT_FILE = "C:/Users/alfa/PycharmProjects/sgr/engine/assets/converted.stf"




def extract_glyph_contours(glyph, font: TTFont) -> List[Contour]:
    glyph_set = font.getGlyphSet()
    recording_pen = RecordingPen()

    try:
        if hasattr(glyph, 'draw'):
            glyph.draw(recording_pen)
        elif hasattr(glyph, 'components'):
            for component in glyph.components:
                base_glyph = glyph_set[component.glyphName]
                base_glyph.draw(recording_pen)
        else:
            raise ValueError(f"Unsupported glyph type: {type(glyph)}")
    except Exception as e:
        logger.error(f"Error extracting glyph contours: {e}")
        return []

    return [recording_pen.value]


def normalize_glyph(contours: List[Contour], font: TTFont, glyph_name: str) -> List[Contour]:
    glyph_set = font.getGlyphSet()
    bounds_pen = BoundsPen(glyph_set)

    try:
        glyph_set[glyph_name].draw(bounds_pen)
    except KeyError:
        logger.error(f"Glyph '{glyph_name}' not found in font")
        return []

    if bounds_pen.bounds:
        x_min, y_min, x_max, y_max = bounds_pen.bounds
        width, height = x_max - x_min, y_max - y_min
        scale = min((TARGET_SIZE - 2 * PADDING) / width, (TARGET_SIZE - 2 * PADDING) / height) if width > 0 and height > 0 else 1
        offset_x = (TARGET_SIZE - width * scale) / 2 - x_min * scale
        offset_y = (TARGET_SIZE - height * scale) / 2 - y_min * scale
    else:
        scale, offset_x, offset_y = 1, PADDING, PADDING

    transform = Transform().translate(offset_x, offset_y).scale(scale)
    return [_transform_contour(contour, transform) for contour in contours]


def _transform_contour(contour: Contour, transform: Transform) -> Contour:
    rec_pen = RecordingPen()
    transform_pen = TransformPen(rec_pen, transform)

    for cmd in contour:
        command, args = cmd if isinstance(cmd, tuple) else (cmd[0], cmd[1:])
        getattr(transform_pen, command)(*args)

    return rec_pen.value


def simplify_contours(contours: List[Contour], tolerance: float) -> List[Contour]:
    return [_simplify_contour(contour, tolerance) for contour in contours]


def _simplify_contour(contour: Contour, tolerance: float) -> Contour:
    simplified_contour = []
    last_point = None
    for cmd in contour:
        command, args = cmd if isinstance(cmd, tuple) else (cmd[0], cmd[1:])
        if command == 'curveTo':
            p0, p1, p2 = args
            if (abs(p0[0] - p1[0]) + abs(p0[1] - p1[1]) +
                abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])) < tolerance:
                simplified_contour.append(('lineTo', (p2,)))
            else:
                simplified_contour.append((command, args))
        elif command == 'lineTo':
            p = args[0]
            if last_point and (abs(p[0] - last_point[0]) + abs(p[1] - last_point[1])) < tolerance:
                continue
            simplified_contour.append((command, args))
        else:
            simplified_contour.append((command, args))

        last_point = args[-1] if args else None
    return simplified_contour


def convert_font_to_stf(input_font: str, output_file: str, chars_to_include: Optional[str] = None, simplify_tolerance: float = SIMPLIFY_TOLERANCE):
    chars_to_include = chars_to_include or (string.ascii_letters + string.digits + string.punctuation + ' ')

    try:
        font = TTFont(input_font)
    except Exception as e:
        logger.error(f"Failed to load font file: {e}")
        return

    cmap = font.getBestCmap()

    with open(output_file, 'w') as f:
        for char in chars_to_include:
            glyph_name = cmap.get(ord(char))
            if not glyph_name:
                logger.warning(f"No glyph found for character '{char}'. Skipping.")
                continue

            glyph = font.getGlyphSet()[glyph_name]
            contours = _process_glyph(glyph, font)

            if not contours:
                logger.warning(f"Empty glyph for character '{char}'. Skipping.")
                continue

            normalized_contours = normalize_glyph(contours, font, glyph_name)
            simplified_contours = simplify_contours(normalized_contours, simplify_tolerance)

            _write_glyph_to_stf(f, char, simplified_contours)

        logger.info(f"Conversion complete. STF file saved as {output_file}")


def _process_glyph(glyph, font: TTFont) -> List[Contour]:
    if hasattr(glyph, 'numberOfContours') and glyph.numberOfContours == 0:
        if hasattr(glyph, 'components'):
            contours = []
            for component in glyph.components:
                base_glyph = font.getGlyphSet()[component.glyphName]
                base_contours = extract_glyph_contours(base_glyph, font)
                contours.extend(base_contours)
            return contours
        else:
            return []
    else:
        return extract_glyph_contours(glyph, font)


def _write_glyph_to_stf(file, char: str, contours: List[Contour]):
    file.write(f"char {char} {{\n")
    file.write("init {\n")

    point_index = 1
    connections = []

    for contour in contours:
        current_connection = []
        for cmd, args in contour:
            if cmd == 'moveTo':
                if current_connection:
                    connections.append(current_connection)
                current_connection = [point_index]
            if cmd in ['moveTo', 'lineTo', 'curveTo', 'qCurveTo']:
                x, y = args[-1]
                file.write(f"{point_index}[{x / TARGET_SIZE:.6f},{1 - y / TARGET_SIZE:.6f}];\n")
                current_connection.append(point_index)
                point_index += 1

        if current_connection:
            if current_connection[0] != current_connection[-1]:
                current_connection.append(current_connection[0])
            connections.append(current_connection)

    file.write("}\n")
    file.write("struct(")
    file.write('/'.join('>'.join(str(p) for p in conn) for conn in connections if conn))
    file.write(")\n")
    file.write("}\n\n")


def main():
    # Use hardcoded values instead of argparse
    input_font = INPUT_FONT
    output_file = OUTPUT_FILE
    chars_to_include = None  # Use default characters
    simplify_tolerance = SIMPLIFY_TOLERANCE

    convert_font_to_stf(input_font, output_file, chars_to_include, simplify_tolerance)


if __name__ == "__main__":
    main()
