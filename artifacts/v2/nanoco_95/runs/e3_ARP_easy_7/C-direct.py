import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    depot_coords = params["depot_coordinates"]
    intersection_coords = params["intersection_coordinates"]
    dist_matrix = params["distance_matrix"]
    required_segments = params["required_segment_relations"]
    num_required = params["num_required_segments"]
    num_intersections = params["num_intersections"]
    num_trucks = params["num_trucks"]

    n = num_intersections  # 8 nodes: 0..7

    # Build distance lookup (symmetric)
    # dist_matrix is indexed [i][j] for i,j in 0..n-1
    def dist(i, j):
        return dist_matrix[i][j]

    # Required segments as frozensets for quick lookup
    req_set = set(frozenset(seg) for seg in required_segments)

    # For the Chinese Postman / Route Inspection problem on an undirected graph:
    # We model this as a directed graph where each undirected edge (i,j) can be
    # traversed in either direction, possibly multiple times.
    # 
    # Decision variables:
    #   x[i,j] = number of times arc (i->j) is traversed (integer >= 0)
    #
    # For each required segment {i,j}: x[i,j] + x[j,i] >= 1
    # Flow balance: sum_j x[i,j] = sum_j x[j,i]  for all i
    # Objective: minimize sum_{i,j} dist(i,j) * x[i,j]
    #
    # We also need connectivity (subtour elimination). We use a lazy constraint
    # approach via callback, or we can reformulate. Given the small size (8 nodes),
    # we use a flow-based subtour elimination.

    model = gp.Model("street_sweeping")
    model.setParam("OutputFlag", 0)
    model.setParam("LazyConstraints", 1)

    # Arc variables x[i,j] for i != j
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(dist(i, j) * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance at each node
    for node in range(n):
        model.addConstr(
            gp.quicksum(x[node, j] for j in range(n) if j != node) ==
            gp.quicksum(x[j, node] for j in range(n) if j != node),
            name=f"flow_balance_{node}"
        )

    # Each required segment must be traversed at least once (in either direction)
    for seg in required_segments:
        seg_list = list(seg)
        i, j = seg_list[0], seg_list[1]
        model.addConstr(
            x[i, j] + x[j, i] >= 1,
            name=f"req_seg_{i}_{j}"
        )

    # The tour must depart from depot: total outflow from depot >= 1
    model.addConstr(
        gp.quicksum(x[0, j] for j in range(1, n)) >= 1,
        name="depot_departs"
    )

    # Subtour elimination via lazy constraints (callback)
    def subtour_callback(model_cb, where):
        if where == GRB.Callback.MIPSOL:
            x_val = model_cb.cbGetSolution(x)
            # Build adjacency from arcs with positive flow
            # Find connected components using only nodes with nonzero flow
            active_nodes = set()
            adj = {i: [] for i in range(n)}
            for (i, j) in arcs:
                if x_val[i, j] > 0.5:
                    adj[i].append(j)
                    adj[j]  # ensure key exists
                    active_nodes.add(i)
                    active_nodes.add(j)

            if not active_nodes:
                return

            # BFS/DFS from depot to find reachable nodes
            visited = set()
            stack = [0]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                for nb in adj[node]:
                    if nb not in visited:
                        stack.append(nb)

            # If not all active nodes are reachable from depot, add cut
            unreachable = active_nodes - visited
            if unreachable:
                # Add subtour elimination: for the unreachable component S,
                # sum of arcs leaving S must be >= 1
                # Find the component containing an unreachable node
                component_start = next(iter(unreachable))
                component = set()
                stack2 = [component_start]
                # BFS on undirected version of active arcs
                undirected_adj = {i: set() for i in range(n)}
                for (i, j) in arcs:
                    if x_val[i, j] > 0.5:
                        undirected_adj[i].add(j)
                        undirected_adj[j].add(i)
                while stack2:
                    nd = stack2.pop()
                    if nd in component:
                        continue
                    component.add(nd)
                    for nb in undirected_adj[nd]:
                        if nb not in component:
                            stack2.append(nb)

                # Cut: at least one arc must go from component to outside
                outside = set(range(n)) - component
                cut_arcs = [(i, j) for i in component for j in outside if (i, j) in set(arcs)]
                if cut_arcs:
                    model_cb.cbLazy(
                        gp.quicksum(x[i, j] for (i, j) in cut_arcs) >= 1
                    )

    model.optimize(subtour_callback)

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}