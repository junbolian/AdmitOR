import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    n = len(supply)
    warehouses = range(n)

    # Determine surpluses and deficits
    # surplus[i] = max(0, supply[i] - demand[i])
    # deficit[i] = max(0, demand[i] - supply[i])
    # We model flow x[i][j] = units shipped from i to j
    # Each warehouse can ship out up to its surplus and must receive enough to cover deficit

    model = gp.Model("warehouse_reallocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from warehouse i to warehouse j
    x = {}
    for i in warehouses:
        for j in warehouses:
            if i != j:
                c = cost[i][j]
                if c is not None:
                    x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total shipping cost
    obj = gp.quicksum(cost[i][j] * x[i, j] for (i, j) in x)
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance constraints:
    # For each warehouse i:
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    # Equivalently: outflow[i] - inflow[i] <= supply[i] - demand[i]
    for i in warehouses:
        inflow = gp.quicksum(x[j, i] for j in warehouses if (j, i) in x)
        outflow = gp.quicksum(x[i, j] for j in warehouses if (i, j) in x)
        net_supply = supply[i] - demand[i]
        # supply[i] + inflow - outflow >= demand[i]
        # => inflow - outflow >= demand[i] - supply[i]
        # => outflow - inflow <= supply[i] - demand[i]
        model.addConstr(outflow - inflow <= net_supply, name=f"balance_{i}")

    # Also ensure we don't ship out more than available (supply + inflow)
    # This is implicitly handled since x >= 0 and the balance constraint limits outflow

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}