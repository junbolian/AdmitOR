import gurobipy as gp
from gurobipy import GRB
import random

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    producer_min_delivery = params["producer_min_delivery"]
    cost_min = params["cost_min"]
    cost_max = params["cost_max"]
    cost_p0_c0 = params["cost_p0_c0"]
    cost_p0_c1 = params["cost_p0_c1"]

    num_producers = 6
    num_contracts = 6

    # Build cost matrix: use given values for (0,0) and (0,1),
    # fill others uniformly in [cost_min, cost_max] using a seeded RNG for reproducibility
    rng = random.Random(42)
    cost = {}
    for p in range(num_producers):
        for c in range(num_contracts):
            if p == 0 and c == 0:
                cost[p, c] = cost_p0_c0
            elif p == 0 and c == 1:
                cost[p, c] = cost_p0_c1
            else:
                cost[p, c] = rng.uniform(cost_min, cost_max)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p,c]: electricity delivered by producer p to contract c
    x = model.addVars(num_producers, num_contracts, lb=0.0, name="x")

    # y[p,c]: binary, 1 if producer p contributes to contract c
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[p, c] * x[p, c] for p in range(num_producers) for c in range(num_contracts)),
        GRB.MINIMIZE
    )

    # Capacity constraints: total delivery by producer p <= capacity
    for p in range(num_producers):
        model.addConstr(
            gp.quicksum(x[p, c] for c in range(num_contracts)) <= producer_capacity[p],
            name=f"cap_p{p}"
        )

    # Contract fulfillment: total delivery to contract c >= demand
    for c in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[p, c] for p in range(num_producers)) >= contract_demand[c],
            name=f"demand_c{c}"
        )

    # Minimum contributors per contract
    for c in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[p, c] for p in range(num_producers)) >= min_producers_per_contract[c],
            name=f"min_contrib_c{c}"
        )

    # Minimum delivery if contributing, and linking x to y
    for p in range(num_producers):
        for c in range(num_contracts):
            # x[p,c] >= producer_min_delivery[p] * y[p,c]
            model.addConstr(
                x[p, c] >= producer_min_delivery[p] * y[p, c],
                name=f"min_del_p{p}_c{c}"
            )
            # x[p,c] <= capacity[p] * y[p,c]  (force y=1 if x>0)
            model.addConstr(
                x[p, c] <= producer_capacity[p] * y[p, c],
                name=f"link_p{p}_c{c}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}