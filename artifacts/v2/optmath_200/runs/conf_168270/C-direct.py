import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pattern_yields = params["pattern_yields"]
    demands = params["demands"]
    pattern_upper_bounds = params["pattern_upper_bounds"]

    num_patterns = len(pattern_upper_bounds)
    num_clients = len(demands)

    model = gp.Model("cutting_stock")
    model.setParam("OutputFlag", 0)

    # Decision variables: how many times each pattern is used
    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Upper bounds on pattern usage
    for p in range(num_patterns):
        x[p].ub = pattern_upper_bounds[p]

    # Objective: minimize total rolls used
    model.setObjective(gp.quicksum(x[p] for p in range(num_patterns)), GRB.MINIMIZE)

    # Demand constraints: sheets produced for each client >= demand
    for c in range(num_clients):
        model.addConstr(
            gp.quicksum(pattern_yields[p][c] * x[p] for p in range(num_patterns)) >= demands[c],
            name=f"demand_client_{c}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}