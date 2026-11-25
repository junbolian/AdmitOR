import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_matrix = params["cost_matrix"]

    num_producers = 6
    num_contracts = 7
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = MWh allocated from producer i to contract j
    x = model.addVars(producers, contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(producers, contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Producer capacity constraints
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= producer_capacity[i],
            name=f"capacity_{i}"
        )

    # Contract demand constraints
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors per contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= min_contributors[j],
            name=f"min_contrib_{j}"
        )

    # Linking constraints: x[i,j] > 0 => y[i,j] = 1, with min delivery if contributing
    for i in producers:
        for j in contracts:
            # If y[i,j]=1, x[i,j] >= producer_min_delivery[i]
            model.addConstr(
                x[i, j] >= producer_min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            # If y[i,j]=0, x[i,j] = 0
            model.addConstr(
                x[i, j] <= producer_capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
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