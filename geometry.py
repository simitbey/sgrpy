import math



class Vertices:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __str__(self):
        return f'({self.x}, {self.y})'

class Point3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Triangle:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def area(self):
        ab = self.a.distance(self.b)
        bc = self.b.distance(self.c)
        ca = self.c.distance(self.a)
        s = (ab + bc + ca) / 2
        return (s * (s - ab) * (s - bc) * (s - ca)) ** 0.5

    def perimeter(self):
        return self.a.distance(self.b) + self.b.distance(self.c) + self.c.distance(self.a)

    def __str__(self):
        return f'{self.a}, {self.b}, {self.c}'

class Quadrilateral:
    def __init__(self, a, b, c, d):
        self.triangles = [Triangle(a, b, c), Triangle(a, c, d)]

    def area(self):
        return sum(triangle.area() for triangle in self.triangles)

    def perimeter(self):
        return sum(triangle.perimeter() for triangle in self.triangles) / 2

    def __str__(self):
        return f'{self.triangles[0]}, {self.triangles[1]}'

class Cube:
    def __init__(self, vertices):
        self.triangles = [
            Triangle(vertices[0], vertices[1], vertices[2]), Triangle(vertices[0], vertices[2], vertices[3]),
            Triangle(vertices[4], vertices[5], vertices[6]), Triangle(vertices[4], vertices[6], vertices[7]),
            Triangle(vertices[0], vertices[1], vertices[5]), Triangle(vertices[0], vertices[5], vertices[4]),
            Triangle(vertices[2], vertices[3], vertices[7]), Triangle(vertices[2], vertices[7], vertices[6]),
            Triangle(vertices[1], vertices[2], vertices[6]), Triangle(vertices[1], vertices[6], vertices[5]),
            Triangle(vertices[0], vertices[3], vertices[7]), Triangle(vertices[0], vertices[7], vertices[4])
        ]

    def volume(self):
        edge_length = self.triangles[0].a.distance(self.triangles[0].b)
        return edge_length ** 3

    def surface_area(self):
        return sum(triangle.area() for triangle in self.triangles)

    def __str__(self):
        return f'{self.triangles}'

class CustomShape:
    def __init__(self, triangles):
        self.triangles = triangles

    def area(self):
        return sum(triangle.area() for triangle in self.triangles)

    def perimeter(self):
        edges = set()
        for triangle in self.triangles:
            edges.add((triangle.a, triangle.b))
            edges.add((triangle.b, triangle.c))
            edges.add((triangle.c, triangle.a))
        return sum(edge[0].distance(edge[1]) for edge in edges)

    def __str__(self):
        return f'{self.triangles}'

class ShapeFactory:
    @staticmethod
    def create_cube(center, side_length):
        '''vertices = [Point3D(-1 * scale_factor, -1 * scale_factor, -1 * scale_factor),
                    Point3D(1 * scale_factor, -1 * scale_factor, -1 * scale_factor),
                    Point3D(1 * scale_factor, 1 * scale_factor, -1 * scale_factor),
                    Point3D(-1 * scale_factor, 1 * scale_factor, -1 * scale_factor),
                    Point3D(-1 * scale_factor, -1 * scale_factor, 1 * scale_factor),
                    Point3D(1 * scale_factor, -1 * scale_factor, 1 * scale_factor),
                    Point3D(1 * scale_factor, 1 * scale_factor, 1 * scale_factor),
                    Point3D(-1 * scale_factor, 1 * scale_factor, 1 * scale_factor)]'''

        half_side = side_length / 2
        vertices = [
            Point3D(center.x - half_side, center.y - half_side, center.z - half_side),
            Point3D(center.x + half_side, center.y - half_side, center.z - half_side),
            Point3D(center.x + half_side, center.y + half_side, center.z - half_side),
            Point3D(center.x - half_side, center.y + half_side, center.z - half_side),
            Point3D(center.x - half_side, center.y - half_side, center.z + half_side),
            Point3D(center.x + half_side, center.y - half_side, center.z + half_side),
            Point3D(center.x + half_side, center.y + half_side, center.z + half_side),
            Point3D(center.x - half_side, center.y + half_side, center.z + half_side)
        ]
        return Cube(vertices)

    @staticmethod
    def create_quadrilateral(v1, v2, v3, v4):
        return Quadrilateral(v1, v2, v3, v4)

    @staticmethod
    def create_triangle(v1, v2, v3):
        return Triangle(v1, v2, v3)

    @staticmethod
    def create_square(center, side_length):
        half_side = side_length / 2
        v1 = Point3D(center.x - half_side, center.y - half_side, center.z)
        v2 = Point3D(center.x + half_side, center.y - half_side, center.z)
        v3 = Point3D(center.x + half_side, center.y + half_side, center.z)
        v4 = Point3D(center.x - half_side, center.y + half_side, center.z)
        return ShapeFactory.create_quadrilateral(v1, v2, v3, v4)

    @staticmethod
    def create_custom_shape(vertices):
        if len(vertices) < 3:
            raise ValueError("A shape must have at least 3 vertices")
        triangles = []
        for i in range(1, len(vertices) - 1):
            triangles.append(Triangle(vertices[0], vertices[i], vertices[i + 1]))
        return CustomShape(triangles)

    '''
    @staticmethod
    def create_pyramid(base_center, base_side_length, height):
        base = ShapeFactory.create_square(base_center, base_side_length)
        apex = Point3D(base_center.x, base_center.y, base_center.z + height)
        triangles = base.triangles + [Triangle(base_center, base.triangles[i].a, apex) for i in range(len(base.triangles))]
        return CustomShape(triangles)
    ''' #old pyramid

    @staticmethod
    def create_pyramid(base_center, base_side_length, height):
        base = ShapeFactory.create_square(base_center, base_side_length)
        apex = Point3D(base_center.x, base_center.y, base_center.z + height)
        triangles = base.triangles + [Triangle(base.triangles[i // 2].a, base.triangles[i // 2].b if i % 2 == 0 else base.triangles[i // 2].c, apex) for i in range(4)]
        return CustomShape(triangles)


    @staticmethod
    def create_cube_custom(vertices):
        if len(vertices) != 8:
            raise ValueError("A cube must have 8 vertices")
        return Cube(vertices)

class Display:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def to_screen(self, point):
        return int(point.x + self.width / 2), int(self.height / 2 - point.y)

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

    def project_3d_to_2d(self, point3d):
        factor = 200 / (point3d.z + 200)
        x = point3d.x * factor
        y = point3d.y * factor
        return Vertices(x, y)