import gurobipy as gp
from gurobipy import GRB

def solve(params):
    max_cap = params["max_turbines_per_feeder"]
    cost_matrix = params["cable_cost_matrix"]
    node_coords = params["node_coordinates"]

    n = 16
    nodes = list(range(n))
    substation = 0
    turbines = list(range(1, n))

    # All directed edges (i->j) for i != j
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i,j] = 1 if directed edge i->j is in the tree (i is parent of j)
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # f[i,j] = flow from substation through edge i->j
    # Flow represents number of turbines in subtree rooted at j
    f = model.addVars(edges, vtype=GRB.CONTINUOUS, lb=0, name="f")

    # s[k] = 1 if turbine k is directly connected to substation (feeder root)
    s = model.addVars(turbines, vtype=GRB.BINARY, name="s")

    # g[k,j] = 1 if turbine j belongs to feeder string rooted at k
    # Instead, track feeder load: total turbines in feeder string k
    # We use flow on edges from substation to bound each feeder string
    # Flow on edge (0, k) = number of turbines in feeder string k (including k itself)

    # Objective: minimize total cable cost (undirected, so cost_matrix symmetric)
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE
    )

    # Each non-substation node has exactly one parent
    for j in turbines:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
                        name=f"one_parent_{j}")

    # Substation has no parent
    model.addConstr(gp.quicksum(x[i, 0] for i in turbines) == 0,
                    name="no_parent_substation")

    # Flow conservation: flow into j = (flow out of j) + 1 for turbines
    # flow into substation = 0, flow out = sum of flows to children
    for j in turbines:
        inflow = gp.quicksum(f[i, j] for i in nodes if i != j)
        outflow = gp.quicksum(f[j, k] for k in nodes if k != j)
        model.addConstr(inflow == outflow + 1, name=f"flow_cons_{j}")

    # Flow only on active edges
    for (i, j) in edges:
        model.addConstr(f[i, j] <= (n - 1) * x[i, j], name=f"flow_edge_{i}_{j}")

    # Flow from substation: each outgoing edge from substation carries
    # the subtree size of the feeder string
    for k in turbines:
        model.addConstr(f[0, k] <= max_cap * x[0, k], name=f"feeder_cap_{k}")
        model.addConstr(f[0, k] >= x[0, k], name=f"feeder_min_{k}")

    # Flow must be non-negative and consistent with tree structure
    # (already handled by lb=0 and flow_edge constraints)

    # Total flow out of substation = number of turbines
    model.addConstr(
        gp.quicksum(f[0, k] for k in turbines) == len(turbines),
        name="total_flow"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}