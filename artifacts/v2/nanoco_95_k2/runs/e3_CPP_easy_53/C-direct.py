import gurobipy as gp
from gurobipy import GRB

def solve(params):
    service_cost = params["service_cost"]
    travel_cost = params["travel_cost"]

    n_nodes = 6
    required_edges = [(0,3),(0,4),(1,4),(2,3),(2,5),(3,4),(4,5)]

    # Build travel cost lookup supporting both flat list (36 values) and dict keyed by (i,j)
    def get_tc(i, j):
        if i == j:
            return 0
        if isinstance(travel_cost, dict):
            if (i, j) in travel_cost:
                return travel_cost[(i, j)]
            if (j, i) in travel_cost:
                return travel_cost[(j, i)]
            return 0
        else:
            # flat list: try row-major full matrix first
            lst = list(travel_cost)
            if len(lst) == n_nodes * n_nodes:
                return lst[i * n_nodes + j]
            # otherwise assume upper-triangle without diagonal, packed row by row
            # index for (i,j) with i<j in upper triangle
            if i > j:
                i, j = j, i
            # number of elements before row i: sum_{r=0}^{i-1}(n-1-r)
            idx = 0
            for r in range(i):
                idx += n_nodes - 1 - r
            idx += (j - i - 1)
            return lst[idx]

    # Service cost dict keyed by required edge tuple
    if isinstance(service_cost, dict):
        sc = service_cost
    else:
        sc = {e: list(service_cost)[i] for i, e in enumerate(required_edges)}

    model = gp.Model("route_planning")
    model.setParam("OutputFlag", 0)

    # Directed service traversals on required edges
    s_fwd = {}
    s_bwd = {}
    for e in required_edges:
        s_fwd[e] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"sfwd_{e[0]}_{e[1]}")
        s_bwd[e] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"sbwd_{e[0]}_{e[1]}")

    # Directed deadhead traversals on required edges
    d_fwd = {}
    d_bwd = {}
    for e in required_edges:
        d_fwd[e] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"dfwd_{e[0]}_{e[1]}")
        d_bwd[e] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"dbwd_{e[0]}_{e[1]}")

    # Directed deadhead traversals on non-required arcs
    required_undirected = set(required_edges) | {(v, u) for (u, v) in required_edges}
    dh = {}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j and (i, j) not in required_undirected:
                dh[(i, j)] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"dh_{i}_{j}")

    # Each required edge serviced at least once (either direction)
    for e in required_edges:
        model.addConstr(s_fwd[e] + s_bwd[e] >= 1, name=f"svc_{e[0]}_{e[1]}")

    # Flow conservation at each node
    for node in range(n_nodes):
        out_expr = gp.LinExpr()
        in_expr = gp.LinExpr()

        for e in required_edges:
            u, v = e
            if u == node:
                out_expr += s_fwd[e] + d_fwd[e]
                in_expr  += s_bwd[e] + d_bwd[e]
            if v == node:
                out_expr += s_bwd[e] + d_bwd[e]
                in_expr  += s_fwd[e] + d_fwd[e]

        for (i, j), var in dh.items():
            if i == node:
                out_expr += var
            if j == node:
                in_expr += var

        model.addConstr(in_expr == out_expr, name=f"flow_{node}")

    # Objective
    obj = gp.LinExpr()
    for e in required_edges:
        cost_e = sc[e] if isinstance(sc[e], (int, float)) else float(sc[e])
        tc_e = get_tc(e[0], e[1])
        obj += cost_e * (s_fwd[e] + s_bwd[e])
        obj += tc_e * (d_fwd[e] + d_bwd[e])

    for (i, j), var in dh.items():
        obj += get_tc(i, j) * var

    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}