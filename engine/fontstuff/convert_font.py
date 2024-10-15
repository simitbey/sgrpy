import os
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import argparse
import string
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen


def normalize_glyph(glyph, glyphSet, target_size=1000):
    bounds_pen = BoundsPen(glyphSet)
    glyph.draw(bounds_pen)

    if bounds_pen.bounds:
        xMin, yMin, xMax, yMax = bounds_pen.bounds
        width = xMax - xMin
        height = yMax - yMin
        scale = target_size / max(width, height) if max(width, height) != 0 else 1
        offset_x = -xMin
        offset_y = -yMin
    else:
        scale = 1
        offset_x = offset_y = 0

    transform = Transform().translate(offset_x, offset_y).scale(scale)
    rec_pen = RecordingPen()
    transform_pen = TransformPen(rec_pen, transform)
    glyph.draw(transform_pen)

    return rec_pen.value


def convert_font_to_stf(input_font, output_file):
    font = TTFont(input_font)
    glyphSet = font.getGlyphSet()

    chars_to_include = string.ascii_letters + string.digits + string.punctuation + ' '

    with open(output_file, 'w') as f:
        for char in chars_to_include:
            glyph_name = font.getBestCmap().get(ord(char))
            if glyph_name and glyph_name in glyphSet:
                glyph = glyphSet[glyph_name]
                normalized_glyph = normalize_glyph(glyph, glyphSet)

                # Force a simple shape if the glyph is empty
                if not normalized_glyph:
                    normalized_glyph = [
                        ('moveTo', ((0, 0),)),
                        ('lineTo', ((1000, 0),)),
                        ('lineTo', ((1000, 1000),)),
                        ('lineTo', ((0, 1000),)),
                        ('closePath', ())
                    ]

                f.write(f"char {char} {{\n")
                f.write("init {\n")

                point_index = 1
                connections = []
                current_connection = []

                for cmd, args in normalized_glyph:
                    if cmd == 'moveTo':
                        if current_connection:
                            connections.append(current_connection)
                        current_connection = [point_index]
                        x, y = args[0]
                        f.write(f"{point_index}[{x / 1000:.4f},{1 - y / 1000:.4f}];\n")
                        point_index += 1
                    elif cmd in ['lineTo', 'curveTo']:
                        current_connection.append(point_index)
                        x, y = args[-1]  # Use the last point for both lineTo and curveTo
                        f.write(f"{point_index}[{x / 1000:.4f},{1 - y / 1000:.4f}];\n")
                        point_index += 1
                    elif cmd == 'closePath':
                        if current_connection and current_connection[0] != current_connection[-1]:
                            current_connection.append(current_connection[0])

                if current_connection:
                    connections.append(current_connection)

                f.write("}\n")
                f.write("struct(")
                f.write('/'.join('>'.join(str(p) for p in conn) for conn in connections if conn))
                f.write(")\n")
                f.write("}\n\n")

    print(f"Conversion complete. STF file saved as {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert TTF/OTF fonts to STF format")
    parser.add_argument("input_font", help="Path to the input font file (.ttf or .otf)")
    parser.add_argument("output_file", help="Path to the output .stf file")
    args = parser.parse_args()

    convert_font_to_stf(args.input_font, args.output_file)
