from eval.isobench.loader import IsobenchTask

PROMPT_FOOTER = """
First give an explanation of your answer:
Explanation: <explanation>

Then give your final answer as
ANSWER: <answer>

You should give the final answer without formatting and without any additional information.
"""

MATH_BREAKPOINT_PROMPT = """
You are given a real-valued, scalar function f(x).
YOUR TASK is to count the number of breakpoints in the plot.
A breakpoint refers to a point on the function's domain at which the function's domain at which the funciton changes its slope.
Here is the expression of f(x):
{function}
Respond with the number of breakpoints (in Arab digits) first on how many breakpoints the function f(x) contains based on the definition and your observation of the function.
You should IGNORE the left and right end point of the domain, i.e. if the function is defined on [a, b], you should only consider the domain (a, b).
"""


MATH_CONVEXITY_PROMPT = """
You are given a real-valued, scalar function f(x).
YOUR TASK is to determine whether f(x) is an convex function or concave function.
Definition of a convex function: A function such that for all x, y, and 0 <= t <= 1
f(tx + (1 - t)y) ≤ tf(x) + (1 - t)f(y)
Definition of a concave function: A function such that for all x, y, and 0 <= t <= 1
f(tx + (1 - t)y) ≥ tf(x) + (1 - t)f(y)
Here is the expression of f(x), defined for all x>0.
{function}
Respond with 'convex' or 'concave' first on whether the function f (x) is convex or concave, based on the definitions and your observation of the function.",
"""

GRAPH_ISOMORPHISM_PROMPT = """
You are given two adjacency matrices of graphs G and H.

YOUR TASK is to determine whether the two graphs are isomorphic to each other.
In graph theory, an isomorphism of graphs G and H is a bijection f between the vertex sets of G and H, denoted as f: V(G) -> V(H).
G and H are said to be isomorphic when f satisfies the following: any two vertices u and v of G are adjacent in G if and only if f(u) and f(v) are adjacent in H.
This kind of bijection is commonly described as "edge-preserving bijection," in accordance with the general notion of isomorphism being a structure-preserving bijection.

Adjacency Matrix of Graph G:
{adjacency_matrix_G}

Adjacency Matrix of Graph H:
{adjacency_matrix_H}

Respond with 'True' or 'False' on whether the two graphs are isomorphic to each other.
If they are isomorphic, first provide the bijection between the two graphs, and then explain your reasoning.
If they are not isomorphic, explain why in detail.
"""

GRAPH_CONNECTIVITY_PROMPT = """
You are given an adjacency matrix of a graph and two query nodes.
YOUR TASK is to find if there is a path between the two nodes.

Definition of connectivity: In an undirected graph G, two vertices u and v are called connected if G contains a path from u to v.
A path in a graph is a finite sequence of edges which joins a sequence of vertices.
In the query example, the nodes and the adjacency matrix are zero-indexed.

Query Example:
Adjacency Matrix: {adjacency_matrix}
Query nodes indices (zero-indexed): {query_node_1} and {query_node_2}

If there is a path, provide the path as a sequence of vertices (nodes), and then explain your reasoning.
If there is no path, explain why in details.
Then respond with your final answer as True or False on whether the query nodes are connected or not in the graph.
"""


WINNER_ID_PROMPT = """
Given the following FEN of the chess game:
{fen}
Determine the game's outcome. Who won: White or Black? 
Answer can be 'white', 'black', or 'draw'.
"""


MATH_PARITY_PROMPT = """
"You are given a real-valued, scalar function f(x).
YOUR TASK is to determine whether f(x) is an even function, an odd function, or neither.
Definition of an odd function: A function such that
f(-x) = -f(x)
where the sign is reversed but the absolute value remains the same if the sign of the independent variable is reversed.
A function is neither even nor odd if it does not satisfy either condition.
Here is the expression of f(x):
{function}
Respond with 'even', 'odd', 'neither' first on whether the function f(x) is even, odd, or neither, based on the definitions and your observation of the function.
"""

MAXFLOW_PROMPT = """
You are given an adjacency matrix of a graph and two query nodes. (one source node and one sink node).
The source node is the node where the flow starts and the sink node is the node where the flow ends.
YOUR TASK is to solve the maxflow problem given the weighted directed graph.
In the max flow problem, we have a directed graph with a source node s and a sink node t, 
and each edge has a capacity (integer valued, colored in green) that represents the maximum amount of flow that can be sent through it. 
The goal is to find the maximum amount of flow that can be sent from s to t, while respecting the capacity constraints on the edges.

Query Example:
adjacency matrix:
{adjacency_matrix}
Source node (zero-indexed): {source}
Sink node (zero-indexed): {sink}
In the query example, the nodes are zero-indexed.
Compute the maximum flow from the source node to the sink node.
"""

PROMPT_MAP = {
    IsobenchTask.MATH_BREAKPOINT: MATH_BREAKPOINT_PROMPT,
    IsobenchTask.MATH_CONVEXITY: MATH_CONVEXITY_PROMPT,
    IsobenchTask.MATH_PARITY: MATH_PARITY_PROMPT,
    IsobenchTask.GRAPH_MAXFLOW: MAXFLOW_PROMPT,
    IsobenchTask.GRAPH_ISOMORPHISM: GRAPH_ISOMORPHISM_PROMPT,
    IsobenchTask.GRAPH_CONNECTIVITY: GRAPH_CONNECTIVITY_PROMPT,
    IsobenchTask.WINNER_ID: WINNER_ID_PROMPT,
}


def get_prompt(data: dict, task: IsobenchTask) -> str:
    prompt_template = get_prompt_template(task)
    match task:
        case IsobenchTask.MATH_BREAKPOINT:
            return prompt_template.format(function=data["code"])
        case IsobenchTask.MATH_CONVEXITY:
            return prompt_template.format(function=data["code"])
        case IsobenchTask.GRAPH_ISOMORPHISM:
            return prompt_template.format(
                adjacency_matrix_G=data["adjacency_matrix_G"],
                adjacency_matrix_H=data["adjacency_matrix_H"],
            )
        case IsobenchTask.GRAPH_CONNECTIVITY:
            return prompt_template.format(
                adjacency_matrix=data["adjacency_matrix"],
                query_node_1=data["query_node_1"],
                query_node_2=data["query_node_2"],
            )
        case IsobenchTask.WINNER_ID:
            return prompt_template.format(fen=data["fen"])
        case IsobenchTask.MATH_PARITY:
            return prompt_template.format(function=data["code"])
        case IsobenchTask.GRAPH_MAXFLOW:
            return prompt_template.format(
                adjacency_matrix=data["adjacency_matrix"],
                source=data["source_node"],
                sink=data["sink_node"],
            )
        case _:
            raise ValueError(f"Task {task} not supported.")


def get_prompt_template(task: IsobenchTask) -> str:
    if task in PROMPT_MAP:
        return PROMPT_MAP[task] + PROMPT_FOOTER
    else:
        raise ValueError(f"Task {task} not supported.")
