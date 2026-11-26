import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supplies = params["initial_supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]

    n = 7
    warehouses = range(n)

    model = gp.Model("warehouse_supply")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units shipped from warehouse i to warehouse j
    x = [[None] * n for _ in warehouses]
    for i in warehouses:
        for j in warehouses:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    obj = gp.LinExpr()
    for i in warehouses:
        for j in warehouses:
            if i != j:
                obj += transport_costs[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: initial_supply + inflow - outflow >= demand
    for i in warehouses:
        inflow = gp.quicksum(x[j][i] for j in warehouses if j != i)
        outflow = gp.quicksum(x[i][j] for j in warehouses if j != i)
        model.addConstr(
            initial_supplies[i] + inflow - outflow >= demands[i],
            name=f"balance_{i}"
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