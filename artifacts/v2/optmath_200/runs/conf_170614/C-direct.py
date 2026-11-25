import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [params["capacity_0"], params["capacity_1"], params["capacity_2"]]
    demand = [params["demand_0"], params["demand_1"], params["demand_2"], params["demand_3"]]
    cost = [
        [params["cost_0_0"], params["cost_0_1"], params["cost_0_2"], params["cost_0_3"]],
        [params["cost_1_0"], params["cost_1_1"], params["cost_1_2"], params["cost_1_3"]],
        [params["cost_2_0"], params["cost_2_1"], params["cost_2_2"], params["cost_2_3"]],
    ]
    min_delivery = [params["min_delivery_0"], params["min_delivery_1"], params["min_delivery_2"]]
    min_producers = params["min_producers_per_contract"]

    num_producers = 3
    num_contracts = 4

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j]: amount delivered from producer i to contract j
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{j}") for j in range(num_contracts)] for i in range(num_producers)]
    # y[i][j]: binary, 1 if producer i is assigned to contract j
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}") for j in range(num_contracts)] for i in range(num_producers)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j] for i in range(num_producers) for j in range(num_contracts)),
        GRB.MINIMIZE
    )

    # Capacity constraints
    for i in range(num_producers):
        model.addConstr(gp.quicksum(x[i][j] for j in range(num_contracts)) <= capacity[i], name=f"cap_{i}")

    # Demand constraints
    for j in range(num_contracts):
        model.addConstr(gp.quicksum(x[i][j] for i in range(num_producers)) >= demand[j], name=f"dem_{j}")

    # Minimum delivery if assigned
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i][j] >= min_delivery[i] * y[i][j]
            model.addConstr(x[i][j] >= min_delivery[i] * y[i][j], name=f"min_del_{i}_{j}")
            # x[i][j] <= capacity[i] * y[i][j]  (force y=1 if x>0)
            model.addConstr(x[i][j] <= capacity[i] * y[i][j], name=f"link_{i}_{j}")

    # Minimum producers per contract
    for j in range(num_contracts):
        model.addConstr(gp.quicksum(y[i][j] for i in range(num_producers)) >= min_producers, name=f"min_prod_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}