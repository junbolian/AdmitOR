import gurobipy as gp
from gurobipy import GRB

def solve(params):
    def scalar(v):
        """Return a numeric scalar: use directly if numeric, else take first element."""
        if hasattr(v, '__len__'):
            return float(v[0])
        return float(v)

    net_flow = {
        0: params["net_flow_hub0"],
        1: params["net_flow_hub1"],
        2: params["net_flow_hub2"],
        3: params["net_flow_hub3"],
        4: params["net_flow_hub4"],
    }

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (1, 3), (1, 4),
        (2, 3), (2, 4),
        (3, 4),
    ]

    fc_other = scalar(params["fixed_cost_other"])
    cap_other = scalar(params["capacity_other"])
    vc_other = scalar(params["variable_cost_other"])

    fixed_cost = {
        (0, 1): float(params["fixed_cost_0_1"]),
        (0, 2): float(params["fixed_cost_0_2"]),
        (0, 3): fc_other,
        (0, 4): fc_other,
        (1, 2): fc_other,
        (1, 3): fc_other,
        (1, 4): fc_other,
        (2, 3): fc_other,
        (2, 4): fc_other,
        (3, 4): fc_other,
    }

    capacity = {
        (0, 1): float(params["capacity_0_1"]),
        (0, 2): float(params["capacity_0_2"]),
        (0, 3): cap_other,
        (0, 4): cap_other,
        (1, 2): cap_other,
        (1, 3): cap_other,
        (1, 4): cap_other,
        (2, 3): cap_other,
        (2, 4): cap_other,
        (3, 4): cap_other,
    }

    var_cost = {
        (0, 1): float(params["variable_cost_0_1"]),
        (0, 2): float(params["variable_cost_0_2"]),
        (0, 3): vc_other,
        (0, 4): vc_other,
        (1, 2): vc_other,
        (1, 3): vc_other,
        (1, 4): vc_other,
        (2, 3): vc_other,
        (2, 4): vc_other,
        (3, 4): vc_other,
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: establish connection on undirected edge (i,j)
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")

    # Flow variables in both directions for each undirected edge
    directed_arcs = arcs + [(j, i) for (i, j) in arcs]

    # Map each directed arc to its canonical undirected edge
    edge_of = {}
    for (i, j) in arcs:
        edge_of[(i, j)] = (i, j)
        edge_of[(j, i)] = (i, j)

    f = model.addVars(directed_arcs, lb=0.0, vtype=GRB.CONTINUOUS, name="f")

    # Capacity constraints: flow in either direction bounded by capacity * y
    for (i, j) in arcs:
        cap_ij = capacity[(i, j)]
        model.addConstr(f[i, j] <= cap_ij * y[i, j], name=f"cap_fwd_{i}_{j}")
        model.addConstr(f[j, i] <= cap_ij * y[i, j], name=f"cap_bwd_{i}_{j}")

    # Flow balance at each node: outflow - inflow == net_flow
    # Positive net_flow = demand (net outflow), negative = supply (net inflow)
    for n in range(5):
        outflow = gp.quicksum(f[n, k] for k in range(5) if (n, k) in edge_of)
        inflow  = gp.quicksum(f[k, n] for k in range(5) if (k, n) in edge_of)
        model.addConstr(outflow - inflow == net_flow[n], name=f"balance_{n}")

    # Objective: fixed costs + variable costs
    obj = (
        gp.quicksum(fixed_cost[(i, j)] * y[i, j] for (i, j) in arcs)
        + gp.quicksum(var_cost[edge_of[a]] * f[a] for a in directed_arcs)
    )
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
        return {"objective": None, "status": f"gurobi_status_{status}"}