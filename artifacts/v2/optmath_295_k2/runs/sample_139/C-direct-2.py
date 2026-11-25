import gurobipy as gp
from gurobipy import GRB


def solve(params):
    # Node balances: positive = demand (net outflow), negative = supply (net inflow)
    b = [0.0] * 5
    b[0] = float(params["net_flow_hub0"])
    b[1] = float(params["net_flow_hub1"])
    b[2] = float(params["net_flow_hub2"])
    b[3] = -float(params["net_flow_hub3"])
    b[4] = -float(params["net_flow_hub4"])

    fixed_cost = {}
    capacity = {}
    var_cost = {}

    fixed_cost[(0, 1)] = float(params["fixed_cost_0_1"])
    fixed_cost[(0, 2)] = float(params["fixed_cost_0_2"])
    capacity[(0, 1)] = float(params["capacity_0_1"])
    capacity[(0, 2)] = float(params["capacity_0_2"])
    var_cost[(0, 1)] = float(params["variable_cost_0_1"])
    var_cost[(0, 2)] = float(params["variable_cost_0_2"])

    fc_other = params["fixed_cost_other"]
    cap_other = params["capacity_other"]
    vc_other = params["variable_cost_other"]

    # All directed arcs excluding (0,1) and (0,2), in a stable order
    candidate_arcs = [
        (i, j)
        for i in range(5)
        for j in range(5)
        if i != j and (i, j) not in {(0, 1), (0, 2)}
    ]

    def _norm_key(k):
        if isinstance(k, str):
            p = k.split("_")
            return (int(p[0]), int(p[1]))
        return (int(k[0]), int(k[1]))

    def _get_other(val, arc, idx):
        if isinstance(val, dict):
            if arc in val:
                return float(val[arc])
            skey = f"{arc[0]}_{arc[1]}"
            if skey in val:
                return float(val[skey])
            raise KeyError(f"Missing 'other' value for arc {arc}")
        if isinstance(val, (list, tuple)):
            return float(val[idx])
        # scalar: same value for all arcs
        return float(val)

    # Determine which arcs the "other" parameters actually cover
    if isinstance(fc_other, dict):
        other_arcs = [_norm_key(k) for k in fc_other.keys()]
    elif isinstance(fc_other, (list, tuple)):
        # Use only as many candidate arcs as entries in the list
        n = len(fc_other)
        other_arcs = candidate_arcs[:n]
    else:
        # Scalar: applies to all remaining candidate arcs
        other_arcs = candidate_arcs

    for idx, arc in enumerate(other_arcs):
        fixed_cost[arc] = _get_other(fc_other, arc, idx)
        capacity[arc] = _get_other(cap_other, arc, idx)
        var_cost[arc] = _get_other(vc_other, arc, idx)

    all_arcs = list(fixed_cost.keys())
    arc_set = set(all_arcs)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    y = {}
    x = {}
    for arc in all_arcs:
        y[arc] = model.addVar(vtype=GRB.BINARY, name=f"y_{arc[0]}_{arc[1]}")
        x[arc] = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name=f"x_{arc[0]}_{arc[1]}")

    model.update()

    model.setObjective(
        gp.quicksum(fixed_cost[arc] * y[arc] for arc in all_arcs)
        + gp.quicksum(var_cost[arc] * x[arc] for arc in all_arcs),
        GRB.MINIMIZE,
    )

    for arc in all_arcs:
        model.addConstr(x[arc] <= capacity[arc] * y[arc])

    for i in range(5):
        inflow = gp.quicksum(x[(j, i)] for j in range(5) if (j, i) in arc_set)
        outflow = gp.quicksum(x[(i, j)] for j in range(5) if (i, j) in arc_set)
        model.addConstr(inflow - outflow == b[i])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}