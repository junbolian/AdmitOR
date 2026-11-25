import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["fixed_costs"]
    capacities = params["capacities"]
    demands = params["demands"]
    shipping_costs = params["shipping_costs"]

    num_facilities = 8
    num_customers = 7
    facilities = list(range(num_facilities))
    customers = list(range(num_customers))

    # Normalize fixed_costs to indexed by int
    if isinstance(fixed_costs, dict):
        fc = [fixed_costs[f"facility_{i}"] for i in facilities]
    else:
        fc = list(fixed_costs)

    if isinstance(capacities, dict):
        cap = [capacities[f"facility_{i}"] for i in facilities]
    else:
        cap = list(capacities)

    if isinstance(demands, dict):
        dem = [demands[f"customer_{j}"] for j in customers]
    else:
        dem = list(demands)

    # shipping_costs: rows = facilities, cols = customers
    # Could be list of lists or dict of dicts
    if isinstance(shipping_costs, dict):
        sc = [[shipping_costs[f"facility_{i}"][f"customer_{j}"] for j in customers] for i in facilities]
    else:
        sc = [list(row) for row in shipping_costs]

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    open_vars = model.addVars(facilities, vtype=GRB.BINARY, name="open")
    ship_vars = model.addVars(facilities, customers, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(fc[i] * open_vars[i] for i in facilities) +
        gp.quicksum(sc[i][j] * ship_vars[i, j] for i in facilities for j in customers),
        GRB.MINIMIZE
    )

    for j in customers:
        model.addConstr(
            gp.quicksum(ship_vars[i, j] for i in facilities) == dem[j],
            name=f"demand_{j}"
        )

    for i in facilities:
        model.addConstr(
            gp.quicksum(ship_vars[i, j] for j in customers) <= cap[i] * open_vars[i],
            name=f"capacity_{i}"
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