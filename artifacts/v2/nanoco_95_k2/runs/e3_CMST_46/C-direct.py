import gurobipy as gp
from gurobipy import GRB

def solve(params):
    splitter_port_limit = params["splitter_port_limit"]

    nodes = list(range(16))
    non_hub = list(range(1, 16))

    dist = {}
    for i in range(16):
        for j in range(i + 1, 16):
            key = f"dist_{i}_{j}"
            dist[i, j] = params[key]
            dist[j, i] = params[key]

    model = gp.Model("PON_Network")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 300)

    # Undirected edge selection
    edges = [(i, j) for i in nodes for j in nodes if i < j]
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Directed flow: f[i,j] = total flow from i to j summed over all commodities
    # We use per-commodity flow to enforce tree structure.
    # f[i,j,k] = flow on arc i->j for commodity k (each non-hub node k sends 1 unit to hub 0)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    f = model.addVars(
        [(i, j, k) for (i, j) in arcs for k in non_hub],
        vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0, name="f"
    )

    # Objective
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE
    )

    # Tree has exactly 15 edges
    model.addConstr(gp.quicksum(x[i, j] for (i, j) in edges) == 15, name="tree_size")

    # Flow capacity: flow on arc (i,j) only if edge (i,j) selected
    for i, j in edges:
        for k in non_hub:
            model.addConstr(f[i, j, k] <= x[i, j], name=f"cap_fwd_{i}_{j}_{k}")
            model.addConstr(f[j, i, k] <= x[i, j], name=f"cap_rev_{i}_{j}_{k}")

    # Flow conservation
    for k in non_hub:
        # Source node k: net outflow = 1
        model.addConstr(
            gp.quicksum(f[k, j, k] for j in nodes if j != k)
            - gp.quicksum(f[j, k, k] for j in nodes if j != k) == 1,
            name=f"src_{k}"
        )
        # Hub node 0: net inflow = 1
        model.addConstr(
            gp.quicksum(f[j, 0, k] for j in nodes if j != 0)
            - gp.quicksum(f[0, j, k] for j in nodes if j != 0) == 1,
            name=f"sink_{k}"
        )
        # Intermediate nodes: flow conservation
        for i in nodes:
            if i != k and i != 0:
                model.addConstr(
                    gp.quicksum(f[i, j, k] for j in nodes if j != i)
                    - gp.quicksum(f[j, i, k] for j in nodes if j != i) == 0,
                    name=f"conserve_{i}_{k}"
                )

    # Splitter constraint:
    # For each direct child s of hub, the total flow passing through arc (s->0)
    # across all commodities equals the number of nodes in s's subtree.
    # That must be <= splitter_port_limit.
    for s in non_hub:
        model.addConstr(
            gp.quicksum(f[s, 0, k] for k in non_hub) <= splitter_port_limit * x[0, s],
            name=f"splitter_{s}"
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.objVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.objVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    elif model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": "failed"}