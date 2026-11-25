import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Read numeric parameters
    num_nodes = int(params["num_nodes"])
    depot = int(params["depot"])

    # Required edges and their service costs
    required_edges = [
        (0, 7), (1, 7), (2, 5), (2, 7),
        (3, 6), (3, 7), (4, 6), (5, 6), (5, 7)
    ]
    edge_cost_keys = {
        (0, 7): "edge_cost_0_7",
        (1, 7): "edge_cost_1_7",
        (2, 5): "edge_cost_2_5",
        (2, 7): "edge_cost_2_7",
        (3, 6): "edge_cost_3_6",
        (3, 7): "edge_cost_3_7",
        (4, 6): "edge_cost_4_6",
        (5, 6): "edge_cost_5_6",
        (5, 7): "edge_cost_5_7",
    }
    edge_costs = {e: params[edge_cost_keys[e]] for e in required_edges}

    # Travel distances (full matrix)
    nodes = list(range(num_nodes))
    dist = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                dist[i, j] = 0.0
            elif i < j:
                dist[i, j] = params[f"dist_{i}_{j}"]
                dist[j, i] = params[f"dist_{i}_{j}"]
            # j < i handled by above symmetric assignment

    # Graph edges (undirected, same as required edges here)
    graph_edges = required_edges[:]

    # Build a directed arc set from undirected edges.
    # For each undirected edge (u,v), we have directed arcs (u->v) and (v->u).
    # For required edges, traversal in either direction satisfies the requirement.
    # Decision variables:
    #   x[u,v] = number of times arc (u->v) is traversed (integer >= 0)
    # Service cost for a required edge is incurred once per traversal of either direction.
    # We separate: for required edge (i,j), let:
    #   s[i,j] = 1 if serviced (at least one traversal of (i,j) or (j,i) counts as service)
    # Actually, since all graph edges are required edges, every traversal is a service traversal
    # the first time, then deadhead. The total cost = sum over required edges of (service_cost +
    # deadhead_cost * extra_traversals). But since service cost is a fixed per-traversal cost
    # for the treatment operation, and deadhead is travel without treatment:
    # - First traversal of a required edge (either direction): pays service cost + travel distance
    # - Additional traversals: pays travel distance only (deadhead)
    #
    # This is the Route Inspection / Chinese Postman variant (Rural Postman Problem).
    # Formulation: minimize total traversal cost where required edges must each be traversed >= 1.
    # 
    # We model it as:
    #   x_fwd[e]: traversals of edge e in forward direction (integer >= 0)
    #   x_bwd[e]: traversals of edge e in backward direction (integer >= 0)
    #   For required edge e=(i,j): x_fwd[e] + x_bwd[e] >= 1 (must be serviced)
    #
    # Cost of traversing required edge e once (service): edge_costs[e] (includes travel)
    # Cost of additional traversals (deadhead): dist[i,j]
    # 
    # To avoid a nonlinear "first traversal vs extra" distinction, we reformulate:
    # Total cost = sum_e [ (x_fwd[e] + x_bwd[e]) * dist[i,j] + service_cost[e] * min(1, x_fwd+x_bwd) ]
    # Since x_fwd+x_bwd >= 1 and we want min(1,...), introduce binary y[e] = 1 if serviced.
    # But since all edges are required, y[e]=1 for all e. So:
    # Total cost = sum_e [ (x_fwd[e] + x_bwd[e]) * dist[i,j] + edge_costs[e] ]
    # subject to x_fwd[e] + x_bwd[e] >= 1 for all required e.
    # 
    # Flow conservation at each node (Eulerian condition for the route):
    # For each node v: sum of arcs leaving v = sum of arcs entering v
    # (since we need a closed tour starting/ending at depot)

    model = gp.Model("winter_road_maintenance")
    model.setParam("OutputFlag", 0)

    # Variables: directed traversal counts for each undirected edge
    x_fwd = {}  # x_fwd[e]: traversals of e in direction (e[0] -> e[1])
    x_bwd = {}  # x_bwd[e]: traversals of e in direction (e[1] -> e[0])
    for e in graph_edges:
        x_fwd[e] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_fwd_{e[0]}_{e[1]}")
        x_bwd[e] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_bwd_{e[0]}_{e[1]}")

    # Objective: total travel cost (service cost is fixed since all required, plus traversal distances)
    total_service_cost = sum(edge_costs[e] for e in required_edges)

    obj = gp.LinExpr(total_service_cost)
    for e in graph_edges:
        d = dist[e[0], e[1]]
        obj += d * x_fwd[e] + d * x_bwd[e]
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraints: each required edge traversed at least once (either direction)
    for e in required_edges:
        model.addConstr(x_fwd[e] + x_bwd[e] >= 1, name=f"service_{e[0]}_{e[1]}")

    # Flow conservation at every node: outflow = inflow
    # Build arc lists per node
    out_arcs = {v: [] for v in nodes}
    in_arcs = {v: [] for v in nodes}
    for e in graph_edges:
        u, v = e
        out_arcs[u].append(x_fwd[e])
        in_arcs[v].append(x_fwd[e])
        out_arcs[v].append(x_bwd[e])
        in_arcs[u].append(x_bwd[e])

    for v in nodes:
        out_expr = gp.quicksum(out_arcs[v])
        in_expr = gp.quicksum(in_arcs[v])
        model.addConstr(out_expr == in_expr, name=f"flow_balance_{v}")

    # At least one traversal must occur (the route must be non-trivial)
    # This is guaranteed by the service constraints above.

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}