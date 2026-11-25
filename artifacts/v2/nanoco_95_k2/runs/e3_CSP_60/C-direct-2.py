import gurobipy as gp
from gurobipy import GRB

def solve(params):
    bolt_length = params["bolt_length"]
    L1 = params["strip_length_L1"]
    L2 = params["strip_length_L2"]
    L3 = params["strip_length_L3"]
    L4 = params["strip_length_L4"]
    D1 = params["demand_D1"]
    D2 = params["demand_D2"]
    D3 = params["demand_D3"]
    D4 = params["demand_D4"]

    # Upper bound on bolts needed (worst case: each strip on its own bolt)
    max_bolts = D1 + D2 + D3 + D4

    # Enumerate all feasible cutting patterns:
    # a pattern is (n1, n2, n3, n4) with n1*L1 + n2*L2 + n3*L3 + n4*L4 <= bolt_length
    patterns = []
    for n1 in range(int(bolt_length // L1) + 1):
        for n2 in range(int(bolt_length // L2) + 1):
            for n3 in range(int(bolt_length // L3) + 1):
                for n4 in range(int(bolt_length // L4) + 1):
                    used = n1 * L1 + n2 * L2 + n3 * L3 + n4 * L4
                    if used <= bolt_length and (n1 + n2 + n3 + n4) > 0:
                        patterns.append((n1, n2, n3, n4))

    if not patterns:
        return {"objective": None, "status": "no_feasible_patterns"}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p] = number of bolts cut using pattern p (integer)
    x = model.addVars(len(patterns), vtype=GRB.INTEGER, lb=0, name="x")

    # Minimize total bolts used
    model.setObjective(gp.quicksum(x[p] for p in range(len(patterns))), GRB.MINIMIZE)

    # Demand constraints: each strip type must be satisfied exactly
    model.addConstr(
        gp.quicksum(patterns[p][0] * x[p] for p in range(len(patterns))) >= D1,
        name="demand_L1"
    )
    model.addConstr(
        gp.quicksum(patterns[p][1] * x[p] for p in range(len(patterns))) >= D2,
        name="demand_L2"
    )
    model.addConstr(
        gp.quicksum(patterns[p][2] * x[p] for p in range(len(patterns))) >= D3,
        name="demand_L3"
    )
    model.addConstr(
        gp.quicksum(patterns[p][3] * x[p] for p in range(len(patterns))) >= D4,
        name="demand_L4"
    )

    # Reasonable upper bound to tighten the search
    model.addConstr(
        gp.quicksum(x[p] for p in range(len(patterns))) <= max_bolts,
        name="ub_bolts"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}