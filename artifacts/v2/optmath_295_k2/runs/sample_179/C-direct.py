import random
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_producers = 6
    num_contracts = 6

    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]

    # Build cost matrix: prefer full matrix if provided, else individual
    # entries, else generate deterministically from the cost range.
    if "costs" in params:
        costs = [list(row) for row in params["costs"]]
    else:
        rng = random.Random(0)
        costs = [
            [rng.randint(cost_min, cost_max) for _ in range(num_contracts)]
            for _ in range(num_producers)
        ]
        costs[0][0] = params["cost_p0_c0"]
        costs[0][1] = params["cost_p0_c1"]
        for p in range(num_producers):
            for c in range(num_contracts):
                key = "cost_p{}_c{}".format(p, c)
                if key in params:
                    costs[p][c] = params[key]

    model = gp.Model("energy")
    model.Params.OutputFlag = 0

    # x[p, c]: units producer p delivers to contract c
    # y[p, c]: 1 if producer p contributes to contract c, else 0
    x = {}
    y = {}
    for p in range(num_producers):
        for c in range(num_contracts):
            x[p, c] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS,
                                   name="x_{}_{}".format(p, c))
            y[p, c] = model.addVar(vtype=GRB.BINARY,
                                   name="y_{}_{}".format(p, c))

    model.update()

    # Objective: minimize total generation cost
    model.setObjective(
        gp.quicksum(
            costs[p][c] * x[p, c]
            for p in range(num_producers)
            for c in range(num_contracts)
        ),
        GRB.MINIMIZE,
    )

    # Capacity: total delivery by each producer <= capacity
    for p in range(num_producers):
        model.addConstr(
            gp.quicksum(x[p, c] for c in range(num_contracts))
            <= producer_capacity[p]
        )

    # Demand: total delivery to each contract >= demand
    for c in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[p, c] for p in range(num_producers))
            >= contract_demand[c]
        )

    # Minimum number of producers per contract
    for c in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[p, c] for p in range(num_producers))
            >= min_producers_per_contract[c]
        )

    # Semi-continuous linking constraints:
    #   y = 0  =>  x = 0
    #   y = 1  =>  producer_min_delivery[p] <= x <= producer_capacity[p]
    for p in range(num_producers):
        for c in range(num_contracts):
            model.addConstr(x[p, c] >= producer_min_delivery[p] * y[p, c])
            model.addConstr(x[p, c] <= producer_capacity[p] * y[p, c])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}