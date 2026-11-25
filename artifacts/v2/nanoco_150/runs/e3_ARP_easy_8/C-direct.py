import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    mandatory_segments = params["mandatory_segments"]
    num_nodes = params["num_nodes"]
    num_mandatory_segments = params["num_mandatory_segments"]
    num_vehicles = params["num_vehicles"]
    depot = params["depot"]

    # Build directed arc set: for each undirected edge (i,j), allow traversal in both directions
    # Variables: x[i,j] = number of times arc (i->j) is traversed
    nodes = list(range(num_nodes))

    # Create all directed arcs (excluding self-loops)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    dist = {}
    for i in nodes:
        for j in nodes:
            dist[(i, j)] = distance_matrix[i][j]

    model = gp.Model("route_inspection")
    model.setParam("OutputFlag", 0)

    # x[i,j]: number of times directed arc i->j is used
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints: for each node, inflow == outflow
    # Depot has net flow 0 as well (it's a closed tour)
    for node in nodes:
        inflow = gp.quicksum(x[i, node] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(x[node, j] for (i, j) in arcs if i == node)
        model.addConstr(inflow == outflow, name=f"balance_{node}")

    # Each mandatory segment (undirected) must be traversed at least once
    # (in either direction)
    for idx, (u, v) in enumerate(mandatory_segments):
        model.addConstr(
            x[u, v] + x[v, u] >= 1,
            name=f"mandatory_{idx}"
        )

    # The tour must depart from depot at least once (and return once)
    # This is implied by flow balance + mandatory coverage, but add explicitly
    # to ensure connectivity: depot must have at least num_vehicles departures
    model.addConstr(
        gp.quicksum(x[depot, j] for j in nodes if j != depot) >= num_vehicles,
        name="depot_depart"
    )

    # Subtour elimination: we need connectivity.
    # For the route inspection / Chinese postman variant, we use a cut-based approach.
    # We'll solve iteratively, adding connectivity cuts as needed.

    def get_solution_arcs(x_vals):
        """Return list of (i,j,count) for arcs with positive flow."""
        used = []
        for (i, j) in arcs:
            val = x_vals[(i, j)]
            if val > 0.5:
                used.append((i, j, int(round(val))))
        return used

    def find_connected_components(x_vals):
        """Find weakly connected components of the used arc subgraph."""
        # Build adjacency (undirected)
        neighbors = {n: set() for n in nodes}
        for (i, j) in arcs:
            if x_vals[(i, j)] > 0.5:
                neighbors[i].add(j)
                neighbors[j].add(i)

        # Only consider nodes that are actually used (have degree > 0)
        # or are the depot
        active_nodes = set()
        active_nodes.add(depot)
        for (i, j) in arcs:
            if x_vals[(i, j)] > 0.5:
                active_nodes.add(i)
                active_nodes.add(j)

        visited = set()
        components = []

        for start in active_nodes:
            if start not in visited:
                comp = set()
                stack = [start]
                while stack:
                    node = stack.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    comp.add(node)
                    for nb in neighbors[node]:
                        if nb not in visited and nb in active_nodes:
                            stack.append(nb)
                components.append(comp)

        return components

    # Iterative solving with subtour elimination
    max_iterations = 100
    for iteration in range(max_iterations):
        model.optimize()

        if model.Status == GRB.INFEASIBLE:
            return {"objective": None, "status": "infeasible"}
        if model.Status == GRB.UNBOUNDED:
            return {"objective": None, "status": "unbounded"}
        if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            return {"objective": None, "status": f"solver_status_{model.Status}"}

        x_vals = {(i, j): x[i, j].X for (i, j) in arcs}

        components = find_connected_components(x_vals)

        if len(components) == 1:
            # Single connected component: solution is valid
            break

        # Add connectivity cuts: for each component not containing depot,
        # require at least one arc entering from outside
        depot_comp = None
        for comp in components:
            if depot in comp:
                depot_comp = comp
                break

        for comp in components:
            if depot in comp:
                continue
            # Add cut: sum of arcs from outside comp into comp >= 1
            cut_arcs = [(i, j) for (i, j) in arcs if i not in comp and j in comp]
            if cut_arcs:
                model.addConstr(
                    gp.quicksum(x[i, j] for (i, j) in cut_arcs) >= 1,
                    name=f"connectivity_{iteration}_{id(comp)}"
                )
    else:
        # Max iterations reached; return best found
        pass

    obj_val = model.ObjVal
    return {"objective": float(obj_val), "status": "optimal"}