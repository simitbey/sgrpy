import pygame
import math
from engine.geometry import Display, ShapeFactory, Point3D
import re
import random
import re


class STF:
    def __init__(self, font_file, font_size):
        self.font_size = font_size
        self.characters = self.load_font(font_file)

    def load_font(self, font_file):
        characters = {}
        current_char = None
        current_points = {}
        current_connections = []

        with open(font_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('char'):
                    if current_char:
                        characters[current_char] = {
                            'points': current_points,
                            'connections': current_connections
                        }
                    current_char = line.split()[1]
                    current_points = {}
                    current_connections = []
                elif line.startswith('init'):
                    continue
                elif line.startswith('struct'):
                    struct_content = line[line.index('(') + 1:line.index(')')]
                    for segment in struct_content.split('/'):
                        connection = [int(x) for x in segment.split('>')]
                        current_connections.append(connection)
                elif '[' in line and ']' in line:
                    point_id, coords = line.split('[')
                    point_id = int(point_id)
                    coords = tuple(map(float, coords.strip('];').split(',')))
                    current_points[point_id] = coords

        if current_char:
            characters[current_char] = {
                'points': current_points,
                'connections': current_connections
            }

        return characters

    def get_character_shape(self, char):
        if char not in self.characters:
            return []

        char_data = self.characters[char]
        points = char_data['points']
        connections = char_data['connections']

        shape = []
        for connection in connections:
            connection_points = []
            for point_id in connection:
                if point_id in points:
                    connection_points.append(points[point_id])
                else:
                    print(f"Warning: Point {point_id} not found for character '{char}'")
            if connection_points:
                shape.append(connection_points)

        return shape

    def debug_print(self):
        for char, data in self.characters.items():
            print(f"Character: {char}")
            print(f"  Points: {data['points']}")
            print(f"  Connections: {data['connections']}")
            print("---")


class Transformer:
    def __init__(self):
        self.rotation_angles = {'x': 0, 'y': 0, 'z': 0}
        self.rotation_speed = 0.5

    def rotate_x(self, point, angle):
        rad = math.radians(angle)
        y = point.y * math.cos(rad) - point.z * math.sin(rad)
        z = point.y * math.sin(rad) + point.z * math.cos(rad)
        return Point3D(point.x, y, z)

    def rotate_y(self, point, angle):
        rad = math.radians(angle)
        x = point.x * math.cos(rad) + point.z * math.sin(rad)
        z = -point.x * math.sin(rad) + point.z * math.cos(rad)
        return Point3D(x, point.y, z)

    def rotate_z(self, point, angle):
        rad = math.radians(angle)
        x = point.x * math.cos(rad) - point.y * math.sin(rad)
        y = point.x * math.sin(rad) + point.y * math.cos(rad)
        return Point3D(x, y, point.z)

    def apply_rotation(self, point):
        rotated_point = self.rotate_x(point, self.rotation_angles['x'])
        rotated_point = self.rotate_y(rotated_point, self.rotation_angles['y'])
        rotated_point = self.rotate_z(rotated_point, self.rotation_angles['z'])
        return rotated_point

    def update_rotation(self):
        self.rotation_angles['x'] += self.rotation_speed
        self.rotation_angles['y'] += self.rotation_speed
        self.rotation_angles['z'] += self.rotation_speed

    def adjust_rotation(self, axis, angle):
        self.rotation_angles[axis] += angle

class Renderer:
    def __init__(self, width, height, font_file, font_size=10):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.display = Display(width, height)
        self.clock = pygame.time.Clock()
        self.objects = []
        self.transformer = Transformer()
        self.spinning = False
        self.font = STF(font_file, font_size)
        print(f"Loaded characters: {self.font.characters.keys()}")
        self.rendering_algorithm = 'bresenham'

    def bresenham_line_algorithm(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        sx = -1 if x1 > x2 else 1
        sy = -1 if y1 > y2 else 1

        if dx > dy:
            err = dx / 2.0
            while x != x2:
                self.screen.set_at((x, y), (255, 255, 255))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y2:
                self.screen.set_at((x, y), (255, 255, 255))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

    def midpoint_line_algorithm(self, x1, y1, x2, y2):
        def set_midpoints(x1, y1, x2, y2):
            if abs(x2 - x1) <= 1 and abs(y2 - y1) <= 1:
                return
            mpx = (x1 + x2) // 2
            mpy = (y1 + y2) // 2
            self.screen.set_at((mpx, mpy), (255, 255, 255))

            set_midpoints(x1, y1, mpx, mpy)
            set_midpoints(mpx, mpy, x2, y2)

        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        self.screen.set_at((x1, y1), (255, 255, 255))
        self.screen.set_at((x2, y2), (255, 255, 255))
        set_midpoints(x1, y1, x2, y2)

    def dda_line_algorithm(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        dx = x2 - x1
        dy = y2 - y1
        steps = int(max(abs(dx), abs(dy)))
        x_increment = dx / steps
        y_increment = dy / steps
        x, y = x1, y1
        for _ in range(steps + 1):
            self.screen.set_at((int(x), int(y)), (255, 255, 255))
            x += x_increment
            y += y_increment

    def quantum_line_algorithm(self, x1, y1, x2, y2):
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx**2 + dy**2)
        steps = int(distance)
        x, y = x1, y1

        for _ in range(steps):
            self.screen.set_at((int(x), int(y)), (255, 255, 255))
            deviation = random.uniform(-0.5, 0.5)  # Small random deviation
            x += (dx / steps) + deviation
            y += (dy / steps) + deviation

        self.screen.set_at((int(x2), int(y2)), (255, 255, 255))

    def simit_line_algorithm(self, x1, y1, x2, y2, segment_length=2):
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx ** 2 + dy ** 2)
        steps = int(distance / segment_length)
        x, y = x1, y1

        for _ in range(steps):
            self.screen.set_at((int(x), int(y)), (255, 255, 255))
            x += dx / steps
            y += dy / steps

        self.screen.set_at((int(x2), int(y2)), (255, 255, 255))

    def wu_line_algorithm(self, x0, y0, x1, y1):
        def plot(x, y, c):
            color = (255 * c, 255 * c, 255 * c)
            self.screen.set_at((int(x), int(y)), color)

        def ipart(x):
            return int(x)

        def round(x):
            return ipart(x + 0.5)

        def fpart(x):
            return x - math.floor(x)

        def rfpart(x):
            return 1 - fpart(x)

        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        dx = x1 - x0
        dy = y1 - y0
        gradient = dy / dx if dx != 0 else 1

        xend = round(x0)
        yend = y0 + gradient * (xend - x0)
        xgap = rfpart(x0 + 0.5)
        xpxl1 = xend
        ypxl1 = ipart(yend)
        if steep:
            plot(ypxl1, xpxl1, rfpart(yend) * xgap)
            plot(ypxl1 + 1, xpxl1, fpart(yend) * xgap)
        else:
            plot(xpxl1, ypxl1, rfpart(yend) * xgap)
            plot(xpxl1, ypxl1 + 1, fpart(yend) * xgap)
        intery = yend + gradient

        xend = round(x1)
        yend = y1 + gradient * (xend - x1)
        xgap = fpart(x1 + 0.5)
        xpxl2 = xend
        ypxl2 = ipart(yend)
        if steep:
            plot(ypxl2, xpxl2, rfpart(yend) * xgap)
            plot(ypxl2 + 1, xpxl2, fpart(yend) * xgap)
        else:
            plot(xpxl2, ypxl2, rfpart(yend) * xgap)
            plot(xpxl2, ypxl2 + 1, fpart(yend) * xgap)

        if steep:
            for x in range(xpxl1 + 1, xpxl2):
                plot(ipart(intery), x, rfpart(intery))
                plot(ipart(intery) + 1, x, fpart(intery))
                intery += gradient
        else:
            for x in range(xpxl1 + 1, xpxl2):
                plot(x, ipart(intery), rfpart(intery))
                plot(x, ipart(intery) + 1, fpart(intery))
                intery += gradient

        # Ensure the end points are plotted
        if steep:
            plot(y1, x1, 1)
        else:
            plot(x1, y1, 1)

    def line_renderer(self, x1, y1, x2, y2):
        if self.rendering_algorithm == 'bresenham':
            self.bresenham_line_algorithm(x1, y1, x2, y2)
        elif self.rendering_algorithm == 'midpoint':
            self.midpoint_line_algorithm(x1, y1, x2, y2)
        elif self.rendering_algorithm == 'dda':
            self.bresenham_line_algorithm(x1, y1, x2, y2)
        elif self.rendering_algorithm == 'quantum':
            self.quantum_line_algorithm(x1, y1, x2, y2)
        elif self.rendering_algorithm == 'simit':
            self.simit_line_algorithm(x1, y1, x2, y2)
        elif self.rendering_algorithm == 'wu':
            self.wu_line_algorithm(x1, y1, x2, y2)



    def set_rendering_algorithm(self, algorithm):
        if algorithm in ['bresenham', 'midpoint', 'dda', 'simit','quantum', 'wu']:
            self.rendering_algorithm = algorithm
            print(f"Switched to {algorithm} algorithm")

    def render_character(self, char, position):
        shape = self.font.get_character_shape(char)
        for points in shape:
            for i in range(len(points)):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % len(points)]
                self.line_renderer(
                    position[0] + x1 * self.font.font_size,
                    position[1] + y1 * self.font.font_size,
                    position[0] + x2 * self.font.font_size,
                    position[1] + y2 * self.font.font_size
                )

    def render_text(self, text, position):
        x, y = position
        for char in text:
            self.render_character(char, (x, y))
            x += self.font.font_size * 3

    def get_debug_info(self):
        return [
            "1 2 3 4 5",
        ]

    def render_pixels(self):
        self.screen.fill((0, 0, 0))
        for obj in self.objects:
            transformed_vertices = {}
            for triangle in obj.triangles:
                for vertex in (triangle.a, triangle.b, triangle.c):
                    if vertex not in transformed_vertices:
                        transformed_vertex = self.transformer.apply_rotation(vertex)
                        projected_vertex = self.display.project_3d_to_2d(transformed_vertex)
                        screen_vertex = self.display.to_screen(projected_vertex)
                        transformed_vertices[vertex] = screen_vertex

                vertices = [transformed_vertices[triangle.a], transformed_vertices[triangle.b],
                            transformed_vertices[triangle.c]]
                for i in range(3):
                    self.line_renderer(*vertices[i], *vertices[(i + 1) % 3])

        debug_info = self.get_debug_info()
        for i, line in enumerate(debug_info):
            self.render_text(line, (10, 10 + i * self.font.font_size * 2))

        pygame.display.flip()

    def add_object(self, obj):
        self.objects.append(obj)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.spinning = not self.spinning
                        self.render_pixels()  # Force screen update
                    elif event.key == pygame.K_LEFT:
                        self.transformer.adjust_rotation('y', -5)
                    elif event.key == pygame.K_RIGHT:
                        self.transformer.adjust_rotation('y', 5)
                    elif event.key == pygame.K_UP:
                        self.transformer.adjust_rotation('x', -5)
                    elif event.key == pygame.K_DOWN:
                        self.transformer.adjust_rotation('x', 5)
                    elif event.key == pygame.K_q:
                        self.transformer.adjust_rotation('z', -5)
                    elif event.key == pygame.K_e:
                        self.transformer.adjust_rotation('z', 5)
                    elif event.key == pygame.K_w:
                        self.display.adjust_focal_length(5)
                    elif event.key == pygame.K_s:
                        self.display.adjust_focal_length(-5)
                    elif event.key == pygame.K_p:
                        self.display.toggle_perspective()
                    elif event.key == pygame.K_1:
                        self.set_rendering_algorithm('bresenham')
                    elif event.key == pygame.K_2:
                        self.set_rendering_algorithm('midpoint')
                    elif event.key == pygame.K_3:
                        self.set_rendering_algorithm('dda')
                    elif event.key == pygame.K_4:
                        self.set_rendering_algorithm('simit')
                    elif event.key == pygame.K_5:
                        self.set_rendering_algorithm('quantum')
                    elif event.key == pygame.K_6:
                        self.set_rendering_algorithm('wu')

            if self.spinning:
                self.transformer.update_rotation()
            self.render_pixels()
            self.clock.tick(120)

        pygame.quit()

if __name__ == '__main__':
    renderer = Renderer(1280, 800, 'engine/assets/converted.stf', font_size=10)
    cube1 = ShapeFactory.create_cube(Point3D(0, 0, 0), 60)
    stf = STF('engine/assets/converted.stf', 5)
    stf.debug_print()
    renderer.add_object(cube1)
    renderer.run()