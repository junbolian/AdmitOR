import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    pattern_usage_limit = params["pattern_usage_limit"]
    pattern_yield = params["pattern_yield"]

    num_patterns = 12
    num_widths = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_patterns, vtype=GRB.INTEGER, name="x")

    for p in range(num_patterns):
        model.addConstr(x[p] <= pattern_usage_limit[p], name=f"usage_limit_{p}")

    for w in range(num_widths):
        model.addConstr(
            gp.quicksum(pattern_yield[p][w] * x[p] for p in range(num_patterns)) >= demand[w],
            name=f"demand_{w}"
        )

    model.setObjective(gp.quicksum(x[p] for p in range(num_patterns)), GRB.MINIMIZE)

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