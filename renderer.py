import pygame
import math
from geometry import Display, ShapeFactory, Point3D, Vertices

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

class Renderer:
    def __init__(self, width, height):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.display = Display(width, height)
        self.clock = pygame.time.Clock()
        self.objects = []
        self.transformer = Transformer()
        self.spinning = True  # Flag to control spinning

    def add_object(self, obj):
        self.objects.append(obj)

    def dda_line(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        steps = abs(dx) if abs(dx) > abs(dy) else abs(dy)
        x_inc = dx / steps
        y_inc = dy / steps
        x = x1
        y = y1
        for i in range(steps):
            self.screen.set_at((int(x), int(y)), (255, 255, 255))
            x += x_inc
            y += y_inc

    def bresenham_line(self, x1, y1, x2, y2):
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

                x1, y1 = transformed_vertices[triangle.a]
                x2, y2 = transformed_vertices[triangle.b]
                x3, y3 = transformed_vertices[triangle.c]
                self.bresenham_line(x1, y1, x2, y2)
                self.bresenham_line(x2, y2, x3, y3)
                self.bresenham_line(x3, y3, x1, y1)

        pygame.display.flip()


    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.spinning = not self.spinning

            if self.spinning:
                self.transformer.update_rotation()
            self.render_pixels()
            self.clock.tick(120)

        pygame.quit()

if __name__ == '__main__':
    renderer = Renderer(2560/2, 1600/2)

    # Define custom shape vertices
    v1 = Point3D(0, 0, 0)
    v2 = Point3D(15, 0, 0)
    v3 = Point3D(15, 15, 0)
    v4 = Point3D(0, 15, 0)
    v5 = Point3D(7.5, 20, 0)

    # Create custom shape
    custom_shape = ShapeFactory.create_custom_shape([v1, v2, v3, v4, v5])

    cube1 = ShapeFactory.create_cube(Point3D(0, 0, 0), 60)
    pyramid1 = ShapeFactory.create_pyramid(Point3D(0, 0, 0), 30, 60)

    #renderer.add_object(pyramid1)
    renderer.add_object(cube1)
    renderer.run()
