import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    contract_demand = params["contract_demand"]
    min_delivery = params["min_delivery"]
    min_producers_per_contract = params["min_producers_per_contract"]

    num_producers = 4
    num_contracts = 4
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = electricity amount producer i delivers to contract j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}") for j in contracts] for i in producers]

    # y[i][j] = 1 if producer i is assigned to contract j
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}") for j in contracts] for i in producers]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total delivery by producer i <= capacity[i]
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i][j] for j in contracts) <= capacity[i],
            name=f"capacity_{i}"
        )

    # Demand constraints: total delivery to contract j >= contract_demand[j]
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i][j] for i in producers) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # Minimum producers per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i][j] for i in producers) >= min_producers_per_contract,
            name=f"min_producers_{j}"
        )

    # Linking: x[i][j] >= min_delivery[i] * y[i][j]
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i][j] >= min_delivery[i] * y[i][j],
                name=f"min_delivery_{i}_{j}"
            )

    # Linking: x[i][j] <= capacity[i] * y[i][j]
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i][j] <= capacity[i] * y[i][j],
                name=f"link_upper_{i}_{j}"
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