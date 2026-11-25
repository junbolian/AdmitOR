import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    n = 8  # number of intersections
    nodes = list(range(n))
    depot = 0

    # Required edges (undirected)
    required_edges = [(0,2),(0,6),(1,3),(1,6),(2,4),(2,7),(3,5),(3,7)]

    # This is the Route Inspection / Chinese Postman Problem on an undirected graph,
    # but here only specific edges are required (not all edges).
    # We need to find the minimum cost closed walk starting and ending at depot
    # that traverses each required edge at least once.
    #
    # Approach: Model as a directed multigraph flow problem.
    # For each required edge (u,v), we must traverse it at least once (either direction).
    # We can also traverse any edge (u,v) additional times as "deadhead" moves.
    # The tour must be a closed walk starting/ending at depot.
    #
    # Decision variables:
    #   x[u,v] = number of times we traverse arc (u->v), integer >= 0
    #   For required edges: x[u,v] + x[v,u] >= 1
    #   Flow balance: sum_v x[u,v] = sum_v x[v,u] for all u
    #   Connectivity: the solution must form a single connected tour through depot
    #
    # We use directed arcs. For each undirected pair (i,j), we have arcs i->j and j->i.

    dist = distance_matrix

    # Build arc set: all pairs (i,j) with i != j
    arcs = [(i,j) for i in nodes for j in nodes if i != j]

    model = gp.Model("chinese_postman_required")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = number of traversals of arc i->j
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i,j] for (i,j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance at each node
    for node in nodes:
        out_flow = gp.quicksum(x[node, j] for j in nodes if j != node)
        in_flow = gp.quicksum(x[i, node] for i in nodes if i != node)
        model.addConstr(out_flow == in_flow, name=f"balance_{node}")

    # Each required edge must be traversed at least once (either direction)
    for (u, v) in required_edges:
        model.addConstr(x[u,v] + x[v,u] >= 1, name=f"required_{u}_{v}")

    # The tour must be non-trivial (at least one arc used)
    model.addConstr(gp.quicksum(x[i,j] for (i,j) in arcs) >= 1, name="nontrivial")

    # Solve relaxation first to check feasibility, then add connectivity
    # For connectivity, we use a subtour elimination approach:
    # After solving, check if the solution is connected. If not, add cuts.
    # We use iterative subtour elimination.

    model.optimize()

    def get_solution_arcs(x_vars):
        """Extract arc traversal counts from solution."""
        result = {}
        for (i,j) in arcs:
            val = x_vars[i,j].X
            if val > 0.5:
                result[(i,j)] = round(val)
        return result

    def find_subtours(arc_counts):
        """Find connected components in the multigraph defined by arc_counts."""
        # Build adjacency
        adj = {node: set() for node in nodes}
        for (i,j), cnt in arc_counts.items():
            if cnt > 0:
                adj[i].add(j)
                adj[j].add(i)

        # Find nodes that are actually used
        used_nodes = set()
        for (i,j), cnt in arc_counts.items():
            if cnt > 0:
                used_nodes.add(i)
                used_nodes.add(j)

        if not used_nodes:
            return []

        # BFS/DFS to find components among used nodes
        visited = set()
        components = []
        for start in used_nodes:
            if start not in visited:
                comp = set()
                stack = [start]
                while stack:
                    node = stack.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    comp.add(node)
                    for nb in adj[node]:
                        if nb in visited:
                            continue
                        stack.append(nb)
                components.append(comp)
        return components

    # Iterative subtour elimination
    max_iterations = 50
    for iteration in range(max_iterations):
        if model.Status == GRB.INFEASIBLE:
            return {"objective": None, "status": "infeasible"}
        if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            return {"objective": None, "status": f"solver_status_{model.Status}"}

        arc_counts = get_solution_arcs(x)
        components = find_subtours(arc_counts)

        if len(components) <= 1:
            # Single connected component - we have a valid tour
            break

        # Add subtour elimination cuts for components not containing depot
        cut_added = False
        for comp in components:
            if depot in comp:
                continue
            # This component doesn't contain depot - add connectivity cut
            # At least one arc must go from comp to its complement
            complement = set(nodes) - comp
            model.addConstr(
                gp.quicksum(x[i,j] for i in comp for j in complement if (i,j) in set(arcs)) >= 1,
                name=f"subtour_elim_{iteration}_{min(comp)}"
            )
            cut_added = True

        if not cut_added:
            break

        model.optimize()

    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": f"solver_status_{model.Status}"}

    obj_val = model.ObjVal
    return {"objective": float(obj_val), "status": "optimal"}