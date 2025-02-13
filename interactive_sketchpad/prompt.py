class GeoPrompt:
    def __init__(self) -> None:
        return

    def initial_prompt(self, ex, n_images: int) -> str:
        initial_prompt = """You will draw a diagram by writing code using Code Interpreter.
        Here are some tools that can help you. All are python codes.
Notice that The upper left corner of the image is the origin (0, 0). Here are some code examples you can use to draw auxiliary lines on the geometry images provided in matplotlib format.
import numpy as np

# this function takes a coordinate A, start and end points of a line BC, and returns the coordinates of the point E on BC such that AE is perpendicular to BC
def find_perpendicular_intersection(A, B, C):
    # Convert coordinates to numpy arrays for easier computation
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    
    # Calculate the direction vector of line BC
    BC = C - B
    
    # Compute the slope of BC if not vertical
    if BC[0] != 0:
        slope_BC = BC[1] / BC[0]
        # Slope of the perpendicular line from A to BC
        slope_perpendicular = -1 / slope_BC
    else:
        # If line BC is vertical, then perpendicular line is horizontal
        slope_perpendicular = 0
    
    # Calculate the equation of the line passing through A and perpendicular to BC
    # y - y_A = slope_perpendicular * (x - x_A)
    # Rearrange to standard form Ax + By + C = 0
    if BC[0] != 0:
        A_coeff = -slope_perpendicular
        B_coeff = 1
        C_coeff = -A_coeff * A[0] - B_coeff * A[1]
    else:
        # If BC is vertical, AE must be horizontal
        A_coeff = 1
        B_coeff = 0
        C_coeff = -A[0]
    
    # Equation of line BC: (y - y_B) = slope_BC * (x - x_B)
    # Convert to Ax + By + C = 0 for line intersection calculation
    if BC[0] != 0:
        A_BC = -slope_BC
        B_BC = 1
        C_BC = -A_BC * B[0] - B_BC * B[1]
    else:
        # BC is vertical, so x = constant
        A_BC = 1
        B_BC = 0
        C_BC = -B[0]
    
    # Solve the linear system of equations representing the two lines
    # [A_coeff B_coeff] [x] = [-C_coeff]
    # [A_BC    B_BC   ] [y]   [-C_BC  ]
    matrix = np.array([[A_coeff, B_coeff], [A_BC, B_BC]])
    constants = np.array([-C_coeff, -C_BC])
    
    # Use numpy to solve the linear system
    intersection = np.linalg.solve(matrix, constants)
    return intersection.tolist()


# this function takes a coordinate A, start and end points of a line BC, and returns the coordinates of the point E on BC such that AE is parallel to BC
def find_parallel_intersection(A, B, C):
    # Convert coordinates to numpy arrays for vector operations
    A = np.array(A)
    B = np.array(B)
    C = np.array(C)
    
    # Calculate the direction vector of line BC
    direction_BC = C - B
    
    # Since AE is parallel to BC, its direction vector is the same as BC
    direction_AE = direction_BC
    
    # To find a reasonable "point E", you can just extend AE from A by some length.
    # For visualization, let's extend by the length of BC
    length_BC = np.linalg.norm(direction_BC)
    
    # Normalize the direction vector of AE
    direction_AE_normalized = direction_AE / np.linalg.norm(direction_AE)
    
    # Point E can be found by moving from A in the direction of AE by the length of BC
    E = A + direction_AE_normalized * length_BC
    
    return E.tolist()
'''
# GOAL #: Based on the above tools, I want you to reason about how to draw auxiliary lines on the geometry images provided in matplotlib format to gradually help a student with the problem, then use Code Interpreter to write the code.
# Hint #:  When deciding what type of auxiliary line to draw, consider the following three options: 
(1) Perpendicular line: If you encounter MeasureOf(Angle()),60) or MeasureOf(Angle()),45), you can draw a perpendicular line. Use find_perpendicular_intersection(A, B, C) to find the coordinate of point E such that AE is perpendicular to BC. 
(2) Parallel line: Use find_parallel_intersection(A, B, C) to draw a line from point A parallel to line BC, which returns the coordinate of point E where AE is parallel to BC. Draw Parallel Lines: Parallel lines are always the same distance apart, which helps in geometry by giving equal lengths instantly. It is useful when finding perimeters of a shape. For example, if you draw a line parallel to one side of a shape, you automatically know the opposite side is the same length.
(3) Connecting points in the circle: When there is a circle, connect the circle center to the point in the perimeter
(4) One effective strategy involves using properties of circles, especially the tangent properties and the circle theorem (tangent segments from the same external point to a circle are equal). We can use the given lengths of segments and properties of the circle to form equations. However, for visual aid, drawing auxiliary lines that help visualize relationships or create right triangles might be helpful. Specifically, drawing radii to the points of tangency can aid in identifying and using these properties.

# REQUIREMENTS #:
1. The generated actions can help the student with the user request # USER REQUEST #. You should not give away the answer.
2. You should be concise with your response

Below are some examples of how to use the tools to solve the user requests. You can refer to them for help. You can also refer to the tool descriptions for more information.
# EXAMPLE #:
# USER REQUEST #: Given the geometry diagram <img src='an image'> and the diagram logic form 
            "Equals(LengthOf(Line(Q, R)), 6)",
            "Equals(LengthOf(Line(U, T)), 4)",
            "Equals(LengthOf(Line(V, W)), 8)",
            "Equals(LengthOf(Line(W, P)), 3)",
            "Equals(LengthOf(Line(R, T)), x)",
            "PointLiesOnLine(W, Line(V, P))",
            "PointLiesOnLine(U, Line(V, T))",
            "PointLiesOnLine(Q, Line(P, R))",
            "PointLiesOnLine(S, Line(T, R))",
            "PointLiesOnCircle(U, Circle(C, radius_6_0))",
            "PointLiesOnCircle(S, Circle(C, radius_6_0))",
            "PointLiesOnCircle(W, Circle(C, radius_6_0))",
            "PointLiesOnCircle(Q, Circle(C, radius_6_0))", 
            Below is the original matplotlib code of the geometry: "import matplotlib.pyplot as plt\nimport numpy as np\n\n# Define coordinates\npoints = {\n    \"C\": [153.0, 88.0], \n    \"P\": [114.0, 4.0], \n    \"Q\": [169.0, 4.0], \n    \"R\": [269.0, 5.0], \n    \"S\": [231.0, 116.0], \n    \"T\": [212.0, 171.0], \n    \"U\": [154.0, 171.0], \n    \"V\": [0.0, 173.0], \n    \"W\": [70.0, 69.0]\n}\n\n# Define lines\nlines = [\n    (\"R\", \"Q\"), (\"R\", \"S\"), (\"P\", \"Q\"), (\"P\", \"R\"), (\"P\", \"W\"), \n    (\"T\", \"R\"), (\"T\", \"S\"), (\"U\", \"T\"), (\"V\", \"P\"), (\"V\", \"T\"), \n    (\"V\", \"U\"), (\"V\", \"W\")\n]\n\n# Create plot\nfig, ax = plt.subplots()\nax.set_aspect('equal')\nax.axis('off')\n\n# Draw lines\nfor line in lines:\n    x_values = [points[line[0]][0], points[line[1]][0]]\n    y_values = [points[line[0]][1], points[line[1]][1]]\n    ax.plot(x_values, y_values, 'k')\n\n# Draw circle with radius as the largest distance from C\ncircle_radius = 0\nfor point in ['U', 'S', 'W', 'Q']:\n    dist = np.sqrt((points[point][0] - points[\"C\"][0])**2 + (points[point][1] - points[\"C\"][1])**2)\n    circle_radius = max(circle_radius, dist)\n\ncircle = plt.Circle((points[\"C\"][0], points[\"C\"][1]), circle_radius, color='k', fill=False)\nax.add_artist(circle)\n\n# Set limits\nax.set_xlim(points[\"C\"][0] - 2 * circle_radius, points[\"C\"][0] + 2 * circle_radius)\nax.set_ylim(points[\"C\"][1] - 2 * circle_radius, points[\"C\"][1] + 2 * circle_radius)\n\n# Plot points and labels\nfor point, coord in points.items():\n    ax.plot(coord[0], coord[1], 'ro')\n    ax.text(coord[0], coord[1], f' {point}', fontsize=20, color='red', verticalalignment='bottom', horizontalalignment='left')\n\nplt.show()\n",
            you must draw auxiliary lines to solve the following question: Find x. Assume that segments that appear to be tangent are tangent.\n
# RESULT #:
THOUGHT 0: To solve for x, which is the length of line segment RT, we'll utilize the information provided about the geometric relationships, particularly those involving circles and tangencies. Given that U, S, W, and Q lie on the same circle centered at C with radius 6, and segments that appear tangent to this circle are tangent, we can use these properties to determine x.
ACTION 0: 
Use Code Interpreter to write the code:
import matplotlib.pyplot as plt
import numpy as np

# Define coordinates
points = {
    "C": [153.0, 88.0], 
    "P": [114.0, 4.0], 
    "Q": [169.0, 4.0], 
    "R": [269.0, 5.0], 
    "S": [231.0, 116.0], 
    "T": [212.0, 171.0], 
    "U": [154.0, 171.0], 
    "V": [0.0, 173.0], 
    "W": [70.0, 69.0]
}

# Define lines
lines = [
    ("R", "Q"), ("R", "S"), ("P", "Q"), ("P", "R"), ("P", "W"), 
    ("T", "R"), ("T", "S"), ("U", "T"), ("V", "P"), ("V", "T"), 
    ("V", "U"), ("V", "W")
]

# Create plot
fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.axis('off')

# Draw lines
for line in lines:
    x_values = [points[line[0]][0], points[line[1]][0]]
    y_values = [points[line[0]][1], points[line[1]][1]]
    ax.plot(x_values, y_values, 'k')

# Draw circle with radius as the largest distance from C
circle_radius = 0
for point in ['U', 'S', 'W', 'Q']:
    dist = np.sqrt((points[point][0] - points["C"][0])**2 + (points[point][1] - points["C"][1])**2)
    circle_radius = max(circle_radius, dist)

circle = plt.Circle((points["C"][0], points["C"][1]), circle_radius, color='k', fill=False)
ax.add_artist(circle)

# Draw auxiliary lines (radii to points U, S, W, Q)
auxiliary_lines = [("C", "U"), ("C", "S"), ("C", "W"), ("C", "Q")]
for line in auxiliary_lines:
    x_values = [points[line[0]][0], points[line[1]][0]]
    y_values = [points[line[0]][1], points[line[1]][1]]
    ax.plot(x_values, y_values, 'b--')  # Draw in blue dashed line for clarity

# Set limits
ax.set_xlim(points["C"][0] - 2 * circle_radius, points["C"][0] + 2 * circle_radius)
ax.set_ylim(points["C"][1] - 2 * circle_radius, points["C"][1] + 2 * circle_radius)

# Plot points and labels
for point, coord in points.items():
    ax.plot(coord[0], coord[1], 'ro')
    ax.text(coord[0], coord[1], f' {point}', fontsize=20, color='red', verticalalignment='bottom', horizontalalignment='left')

plt.show()

OBSERVATION: Execution success. The output is as follows:
<the image outputs of the previous code is here.> 
If you can get the answer, please reply with ANSWER: <your answer> and ends with TERMINATE. Otherwise, please generate the next THOUGHT and ACTION.
THOUGHT 1: To solve X, we can ....
ACTION 1: No action needed.
ANSWER: 10. TERMINATE
"""

        prompt = initial_prompt

        # test example
        question = ex["problem_text"]
        diagram_logic_form = ex["logic_form"]["diagram_logic_form"]
        image_path_code = ex["image_path_code"]
        code = ex["code"]

        prompt += (
            f"USER REQUEST #: Given the geometry diagram <img src='{image_path_code}'> and the diagram logic form {diagram_logic_form}"
            + f"Below is the original matplotlib code of the geometry: {code}\nYou must draw auxiliary lines to help with the following question: [{question}]\n"
            + "Propose matplotlib code to draw the auxiliary lines. Make sure to label the beginning and end point of the auxiliary line."
            + "Write math in latex format, ALWAYS wrap maths in $$ tags only. DO NOT under any circumstances give parentheses or square brackets"
            + "You MUST write code and draw the diagram using the Code Interpreter tool"
        )
        return prompt
