import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]
    min_producers = params["min_producers"]

    num_producers = len(capacity)
    num_contracts = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j]: MWh delivered by producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0.0, name="x")
    # y[i,j]: 1 if producer i participates in contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j]
                    for i in range(num_producers)
                    for j in range(num_contracts)),
        GRB.MINIMIZE
    )

    # Capacity: each producer's total allocation across all contracts <= capacity[i]
    for i in range(num_producers):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_contracts)) <= capacity[i],
            name=f"cap_{i}"
        )

    # Demand: each contract must receive at least demand[j] MWh
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_producers)) >= demand[j],
            name=f"demand_{j}"
        )

    # Minimum producers per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_producers[j],
            name=f"min_prod_{j}"
        )

    # Minimum delivery if selected, and link x to y
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i,j] >= min_delivery[i] * y[i,j]
            model.addConstr(
                x[i, j] >= min_delivery[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            # x[i,j] <= capacity[i] * y[i,j]  (forces y=1 when x>0)
            model.addConstr(
                x[i, j] <= capacity[i] * y[i, j],
                name=f"link_{i}_{j}"
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