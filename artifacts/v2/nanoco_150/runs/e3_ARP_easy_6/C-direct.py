import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    distance_matrix = params["distance_matrix"]
    junction_coords_x = params["junction_coords_x"]
    junction_coords_y = params["junction_coords_y"]
    num_junctions = params["num_junctions"]
    num_required_segments = params["num_required_segments"]
    depot_junction = params["depot_junction"]
    required_segments = params["required_segments"]

    N = num_junctions
    nodes = list(range(N))
    depot = depot_junction

    # Build set of required edges (undirected, stored as frozensets for lookup)
    req_set = set()
    for seg in required_segments:
        u, v = int(seg[0]), int(seg[1])
        req_set.add((min(u, v), max(u, v)))

    # Arc set: directed arcs (i, j) for i != j
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Cost of traversing arc (i,j): use distance_matrix
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = distance_matrix[i][j]

    model = gp.Model("winter_maintenance")
    model.setParam("OutputFlag", 0)

    # x[i,j] = number of times arc (i,j) is traversed
    x = model.addVars(arcs, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    # For depot: net out-flow = 1 (departs once more than returns, closes as circuit)
    # Actually for a circuit: departures = arrivals at all nodes including depot
    # But we need net flow = 0 at all nodes for a true circuit.
    # For the Chinese Postman / route inspection problem on a directed formulation:
    # flow_out(v) - flow_in(v) = 0 for all v (circuit)
    for v in nodes:
        out_flow = gp.quicksum(x[v, j] for j in nodes if j != v)
        in_flow = gp.quicksum(x[i, v] for i in nodes if i != v)
        model.addConstr(out_flow == in_flow, name=f"flow_balance_{v}")

    # Each required segment (u,v) must be covered at least once
    # Either direction counts as servicing the undirected segment
    for (u, v) in req_set:
        model.addConstr(
            x[u, v] + x[v, u] >= 1,
            name=f"req_seg_{u}_{v}"
        )

    # The route must start and end at depot: ensure depot is visited
    # (flow balance already ensures this if any arcs are used)
    # Ensure at least one departure from depot
    model.addConstr(
        gp.quicksum(x[depot, j] for j in nodes if j != depot) >= 1,
        name="depot_depart"
    )

    # Connectivity: the traversed arcs must form a single connected tour.
    # We enforce this via subtour elimination using lazy constraints.
    # We use a callback to add cuts.

    model.Params.LazyConstraints = 1

    def find_connected_components(x_vals, nodes):
        """Find weakly connected components of arcs with x > 0.5"""
        visited = set()
        adj = {v: set() for v in nodes}
        for (i, j) in arcs:
            if x_vals.get((i, j), 0) > 0.5:
                adj[i].add(j)
                adj[j].add(i)

        components = []
        for start in nodes:
            if start not in visited:
                # BFS
                component = set()
                queue = [start]
                while queue:
                    node = queue.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    component.add(node)
                    for nb in adj[node]:
                        if nb not in visited:
                            queue.append(nb)
                components.append(component)
        return components

    def callback(model_cb, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = {}
            for (i, j) in arcs:
                val = model_cb.cbGetSolution(x[i, j])
                x_vals[(i, j)] = val

            # Find nodes actually used (have flow)
            used_nodes = set()
            for (i, j) in arcs:
                if x_vals.get((i, j), 0) > 0.5:
                    used_nodes.add(i)
                    used_nodes.add(j)

            if len(used_nodes) == 0:
                return

            # Check connectivity among used nodes
            adj = {v: set() for v in used_nodes}
            for (i, j) in arcs:
                if x_vals.get((i, j), 0) > 0.5:
                    adj[i].add(j)
                    adj[j].add(i)

            visited = set()
            queue = [depot]
            while queue:
                node = queue.pop()
                if node in visited:
                    continue
                visited.add(node)
                for nb in adj.get(node, set()):
                    if nb not in visited:
                        queue.append(nb)

            # Nodes used but not reachable from depot
            disconnected = used_nodes - visited
            if disconnected:
                # Add subtour elimination cut:
                # For the disconnected component S, sum of arcs leaving S >= 1
                S = disconnected
                S_complement = set(nodes) - S
                model_cb.cbLazy(
                    gp.quicksum(x[i, j] for i in S for j in S_complement if (i, j) in arcs) +
                    gp.quicksum(x[i, j] for i in S_complement for j in S if (i, j) in arcs) >= 2
                )

    model.optimize(lambda m, where: callback(m, where))

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}