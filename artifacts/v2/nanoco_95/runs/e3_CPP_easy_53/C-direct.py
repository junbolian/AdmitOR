import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    coordinates = params["coordinates"]
    service_costs = params["service_costs"]
    distance_matrix = params["distance_matrix"]

    # Graph edges (required service edges), indexed 0-6
    graph_edges = [(0,3),(0,4),(1,4),(2,3),(2,5),(3,4),(4,5)]
    num_nodes = 6
    depot = 0

    # Build full distance matrix as a dict
    dist = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            dist[i,j] = distance_matrix[i][j]

    # Service cost per required edge (by index)
    sc = {idx: service_costs[idx] for idx in range(len(graph_edges))}

    # For the Route Inspection / Chinese Postman on a general graph:
    # We model this as a directed arc-flow problem.
    # For each required edge (u,v), we can traverse it in either direction
    # (or both) for service. We also allow deadhead arcs between any pair of nodes.
    #
    # Decision variables:
    #   x[e, d] = number of times required edge e is traversed in direction d
    #             d=0: forward (u->v), d=1: backward (v->u)
    #   y[i,j]  = number of deadhead traversals from i to j (i != j)
    #
    # An edge is "serviced" if x[e,0] + x[e,1] >= 1
    # Service cost is incurred per traversal of a required edge (each traversal costs sc[e])
    # Deadhead cost is dist[i,j] per traversal of deadhead arc (i,j)
    #
    # Flow conservation at each node: total arcs leaving = total arcs entering
    # Connectivity: the vehicle forms a closed Eulerian circuit on the multigraph

    model = gp.Model("route_inspection")
    model.setParam("OutputFlag", 0)

    # x[e, 0] = traversals of edge e in forward direction (u->v)
    # x[e, 1] = traversals of edge e in backward direction (v->u)
    x = {}
    for e_idx, (u, v) in enumerate(graph_edges):
        x[e_idx, 0] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{e_idx}_fwd")
        x[e_idx, 1] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{e_idx}_bwd")

    # y[i,j] = deadhead traversals from i to j
    y = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                y[i,j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"y_{i}_{j}")

    # Each required edge must be serviced at least once (in either direction)
    for e_idx in range(len(graph_edges)):
        model.addConstr(x[e_idx, 0] + x[e_idx, 1] >= 1, name=f"service_{e_idx}")

    # Flow conservation at each node
    for node in range(num_nodes):
        flow_out = gp.LinExpr()
        flow_in = gp.LinExpr()

        # Required edge arcs
        for e_idx, (u, v) in enumerate(graph_edges):
            if u == node:
                flow_out += x[e_idx, 0]  # forward: node -> v
                flow_in  += x[e_idx, 1]  # backward: v -> node
            if v == node:
                flow_out += x[e_idx, 1]  # backward: node -> u
                flow_in  += x[e_idx, 0]  # forward: u -> node

        # Deadhead arcs
        for j in range(num_nodes):
            if j != node:
                flow_out += y[node, j]
                flow_in  += y[j, node]

        model.addConstr(flow_out == flow_in, name=f"flow_conservation_{node}")

    # Connectivity: the multigraph must be connected (Eulerian circuit exists).
    # Flow conservation + at least one traversal through depot ensures connectivity
    # for small instances, but we add a subtour elimination via connectivity cuts.
    # For the Chinese Postman on a small graph we use a simpler approach:
    # enforce that total flow through the network is >= 1 at depot.
    # (Flow conservation + service requirements typically guarantee connectivity here.)

    # Force at least one departure from depot so the route is non-trivial
    depart_depot = gp.LinExpr()
    for e_idx, (u, v) in enumerate(graph_edges):
        if u == depot:
            depart_depot += x[e_idx, 0]
        if v == depot:
            depart_depot += x[e_idx, 1]
    for j in range(num_nodes):
        if j != depot:
            depart_depot += y[depot, j]
    model.addConstr(depart_depot >= 1, name="depot_depart")

    # Objective: minimize total service cost + deadhead cost
    obj = gp.LinExpr()
    for e_idx, (u, v) in enumerate(graph_edges):
        obj += sc[e_idx] * x[e_idx, 0]
        obj += sc[e_idx] * x[e_idx, 1]
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                obj += dist[i,j] * y[i,j]

    model.setObjective(obj, GRB.MINIMIZE)

    # Solve with iterative connectivity enforcement
    # We use a callback-free approach: solve, check connectivity, add cuts if needed
    max_iterations = 20
    for iteration in range(max_iterations):
        model.optimize()

        if model.Status == GRB.INFEASIBLE:
            return {"objective": None, "status": "infeasible"}
        if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            return {"objective": None, "status": f"solver_status_{model.Status}"}

        # Extract solution: build adjacency for connectivity check
        # Build the multigraph of used arcs
        arc_counts = {}
        for e_idx, (u, v) in enumerate(graph_edges):
            fwd = int(round(x[e_idx, 0].X))
            bwd = int(round(x[e_idx, 1].X))
            if fwd > 0:
                arc_counts[(u,v)] = arc_counts.get((u,v), 0) + fwd
            if bwd > 0:
                arc_counts[(v,u)] = arc_counts.get((v,u), 0) + bwd
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    val = int(round(y[i,j].X))
                    if val > 0:
                        arc_counts[(i,j)] = arc_counts.get((i,j), 0) + val

        # Find nodes actually used
        used_nodes = set()
        for (i,j), cnt in arc_counts.items():
            if cnt > 0:
                used_nodes.add(i)
                used_nodes.add(j)

        if not used_nodes:
            return {"objective": None, "status": "no_arcs_in_solution"}

        # Check strong connectivity among used nodes via BFS on undirected graph
        adj = {n: set() for n in used_nodes}
        for (i,j), cnt in arc_counts.items():
            if cnt > 0:
                adj[i].add(j)
                adj[j].add(i)

        # BFS from depot
        visited = {depot}
        queue = [depot]
        while queue:
            cur = queue.pop()
            for nb in adj.get(cur, []):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        disconnected = used_nodes - visited
        if not disconnected:
            # Solution is connected — valid
            break

        # Add connectivity cut: for each disconnected component S not containing depot,
        # require at least one arc crossing from V\S to S
        # Simple cut: sum of arcs entering disconnected set >= 1
        cut_lhs = gp.LinExpr()
        S = disconnected
        complement = used_nodes - S

        for e_idx, (u, v) in enumerate(graph_edges):
            if u in complement and v in S:
                cut_lhs += x[e_idx, 0]
            if v in complement and u in S:
                cut_lhs += x[e_idx, 1]
        for i in complement:
            for j in S:
                if i != j:
                    cut_lhs += y[i, j]

        model.addConstr(cut_lhs >= 1, name=f"connectivity_cut_{iteration}")

    else:
        return {"objective": None, "status": "connectivity_not_achieved"}

    return {"objective": model.ObjVal, "status": "optimal"}