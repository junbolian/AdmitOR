import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_contributors = params["min_contributors"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_matrix = params["cost_matrix"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = gp.Model("energy_allocation")
    model.Params.OutputFlag = 0

    x = {}
    y = {}
    for i in range(num_producers):
        for j in range(num_contracts):
            x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
            y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(num_producers)
            for j in range(num_contracts)
        ),
        GRB.MINIMIZE,
    )

    M = max(producer_capacity)

    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= producer_capacity[i],
            name=f"capacity_{i}",
        )
        for j in range(num_contracts):
            model.addConstr(x[i, j] <= M * y[i, j], name=f"link_upper_{i}_{j}")
            model.addConstr(
                x[i, j] >= producer_min_delivery[i] * y[i, j],
                name=f"link_lower_{i}_{j}",
            )

    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= contract_demand[j],
            name=f"demand_{j}",
        )
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_contributors[j],
            name=f"min_contrib_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}