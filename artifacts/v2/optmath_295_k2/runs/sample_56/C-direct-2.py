import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [
        params["capacity_P0"],
        params["capacity_P1"],
        params["capacity_P2"],
    ]
    demand = [
        params["demand_C0"],
        params["demand_C1"],
        params["demand_C2"],
        params["demand_C3"],
    ]
    min_delivery = [
        params["min_delivery_P0"],
        params["min_delivery_P1"],
        params["min_delivery_P2"],
    ]
    cost = [
        [params["cost_P0_C0"], params["cost_P0_C1"], params["cost_P0_C2"], params["cost_P0_C3"]],
        [params["cost_P1_C0"], params["cost_P1_C1"], params["cost_P1_C2"], params["cost_P1_C3"]],
        [params["cost_P2_C0"], params["cost_P2_C1"], params["cost_P2_C2"], params["cost_P2_C3"]],
    ]

    num_producers = 3
    num_contracts = 4
    producers = range(num_producers)
    contracts = range(num_contracts)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p][c]: amount delivered from producer p to contract c
    x = [[model.addVar(lb=0.0, name=f"x_{p}_{c}") for c in contracts] for p in producers]

    # y[p][c]: binary, 1 if producer p delivers to contract c
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{p}_{c}") for c in contracts] for p in producers]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[p][c] * x[p][c] for p in producers for c in contracts),
        GRB.MINIMIZE
    )

    # Capacity constraints: total delivery by each producer <= capacity
    for p in producers:
        model.addConstr(
            gp.quicksum(x[p][c] for c in contracts) <= capacity[p],
            name=f"capacity_{p}"
        )

    # Demand constraints: total delivery to each contract >= demand
    for c in contracts:
        model.addConstr(
            gp.quicksum(x[p][c] for p in producers) >= demand[c],
            name=f"demand_{c}"
        )

    # At least two producers must serve each contract
    for c in contracts:
        model.addConstr(
            gp.quicksum(y[p][c] for p in producers) >= 2,
            name=f"min_producers_{c}"
        )

    # Minimum delivery linking constraints:
    # x[p][c] >= min_delivery[p] * y[p][c]
    # x[p][c] <= capacity[p] * y[p][c]
    for p in producers:
        for c in contracts:
            model.addConstr(
                x[p][c] >= min_delivery[p] * y[p][c],
                name=f"min_delivery_{p}_{c}"
            )
            model.addConstr(
                x[p][c] <= capacity[p] * y[p][c],
                name=f"link_upper_{p}_{c}"
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