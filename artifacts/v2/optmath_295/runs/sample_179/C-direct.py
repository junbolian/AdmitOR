import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_coefficient = params["cost_coefficient"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    def cost(i, j):
        val = cost_coefficient[i * num_contracts + j]
        return val

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = units delivered by producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i contributes to contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            cost(i, j) * x[i, j]
            for i in range(num_producers)
            for j in range(num_contracts)
        ),
        GRB.MINIMIZE
    )

    # Capacity constraints
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"cap_{i}"
        )

    # Contract demand constraints
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}"
        )

    # Minimum contributors per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_contributors[j],
            name=f"min_contrib_{j}"
        )

    # Minimum delivery and linking constraints
    for i in range(num_producers):
        for j in range(num_contracts):
            model.addConstr(
                x[i, j] >= producer_min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
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