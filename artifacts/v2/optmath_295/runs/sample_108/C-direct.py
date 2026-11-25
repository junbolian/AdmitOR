import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [params["capacity_0"], params["capacity_1"], params["capacity_2"]]
    demand = [params["demand_0"], params["demand_1"], params["demand_2"], params["demand_3"]]
    min_delivery = [params["min_delivery_0"], params["min_delivery_1"], params["min_delivery_2"]]
    cost = [
        [params["cost_0_0"], params["cost_0_1"], params["cost_0_2"], params["cost_0_3"]],
        [params["cost_1_0"], params["cost_1_1"], params["cost_1_2"], params["cost_1_3"]],
        [params["cost_2_0"], params["cost_2_1"], params["cost_2_2"], params["cost_2_3"]],
    ]

    num_producers = 3
    num_contracts = 4
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: energy delivered from producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0.0, name="x")

    # y[i,j]: binary, 1 if producer i participates in contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total production cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in producers for j in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total output of each producer <= capacity
    for i in producers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in contracts) <= capacity[i],
            name=f"capacity_{i}"
        )

    # Demand constraints: total supply to each contract >= demand
    for j in contracts:
        model.addConstr(
            gp.quicksum(x[i, j] for i in producers) >= demand[j],
            name=f"demand_{j}"
        )

    # At least two producers must contribute to each contract
    for j in contracts:
        model.addConstr(
            gp.quicksum(y[i, j] for i in producers) >= 2,
            name=f"min_contributors_{j}"
        )

    # Minimum delivery threshold if producer participates
    # x[i,j] >= min_delivery[i] * y[i,j]
    # x[i,j] <= capacity[i] * y[i,j]  (if not participating, x must be 0)
    for i in producers:
        for j in contracts:
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_delivery_{i}_{j}"
            )
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"participation_ub_{i}_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}