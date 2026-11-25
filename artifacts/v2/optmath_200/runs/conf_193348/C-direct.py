import gurobipy as gp
from gurobipy import GRB

def solve(params):
    producer_capacity = params["producer_capacity"]
    contract_demand = params["contract_demand"]
    contract_min_producers = params["contract_min_producers"]
    producer_min_delivery = params["producer_min_delivery"]
    cost = params["cost"]

    P = len(producer_capacity)
    C = len(contract_demand)

    # Normalize cost to a 2D structure: cost_matrix[p][c]
    # Supports both flat list (row-major) and list-of-lists
    if hasattr(cost[0], '__len__'):
        cost_matrix = [[float(cost[p][c]) for c in range(C)] for p in range(P)]
    else:
        cost_matrix = [[float(cost[p * C + c]) for c in range(C)] for p in range(P)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[p, c] = units delivered by producer p to contract c
    x = model.addVars(P, C, lb=0.0, name="x")
    # y[p, c] = 1 if producer p serves contract c
    y = model.addVars(P, C, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[p][c] * x[p, c] for p in range(P) for c in range(C)),
        GRB.MINIMIZE
    )

    # Producer capacity constraints
    for p in range(P):
        model.addConstr(
            gp.quicksum(x[p, c] for c in range(C)) <= float(producer_capacity[p]),
            name=f"cap_{p}"
        )

    # Contract demand constraints
    for c in range(C):
        model.addConstr(
            gp.quicksum(x[p, c] for p in range(P)) >= float(contract_demand[c]),
            name=f"demand_{c}"
        )

    # Contract minimum producers constraints
    for c in range(C):
        model.addConstr(
            gp.quicksum(y[p, c] for p in range(P)) >= float(contract_min_producers[c]),
            name=f"min_prod_{c}"
        )

    # Minimum delivery and linking constraints
    for p in range(P):
        for c in range(C):
            # x[p,c] >= producer_min_delivery[p] * y[p,c]
            model.addConstr(
                x[p, c] >= float(producer_min_delivery[p]) * y[p, c],
                name=f"min_del_{p}_{c}"
            )
            # x[p,c] <= capacity[p] * y[p,c]  (y=0 forces x=0)
            model.addConstr(
                x[p, c] <= float(producer_capacity[p]) * y[p, c],
                name=f"link_{p}_{c}"
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