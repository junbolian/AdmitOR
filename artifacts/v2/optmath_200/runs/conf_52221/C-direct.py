import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    min_producers_per_contract = params["min_producers_per_contract"]
    unit_cost = params["unit_cost"]
    min_delivery_if_assigned = params["min_delivery_if_assigned"]

    num_producers = len(producer_capacity)
    num_contracts = len(contract_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = electricity delivered by producer i to contract j
    x = model.addVars(num_producers, num_contracts, lb=0.0, name="x")

    # y[i,j] = 1 if producer i is assigned to contract j
    y = model.addVars(num_producers, num_contracts, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(unit_cost[i][j] * x[i, j]
                    for i in range(num_producers)
                    for j in range(num_contracts)),
        GRB.MINIMIZE
    )

    # Producer capacity constraints
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

    # Minimum producers per contract
    for j in range(num_contracts):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(num_producers)) >= min_producers_per_contract[j],
            name=f"min_prod_{j}"
        )

    # Linking constraints: if y[i,j]=1, x[i,j] >= min_delivery_if_assigned[i]
    # if y[i,j]=0, x[i,j] = 0
    for i in range(num_producers):
        for j in range(num_contracts):
            # x[i,j] >= min_delivery_if_assigned[i] * y[i,j]
            model.addConstr(
                x[i, j] >= min_delivery_if_assigned[i] * y[i, j],
                name=f"min_del_{i}_{j}"
            )
            # x[i,j] <= capacity[i] * y[i,j]  (forces x=0 when y=0)
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