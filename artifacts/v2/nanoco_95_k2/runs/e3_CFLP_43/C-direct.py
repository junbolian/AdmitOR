import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_costs = params["locker_fixed_costs"]
    capacities = params["locker_capacities"]
    demands = params["customer_demands"]
    cost_matrix = params["delivery_cost_matrix"]
    num_lockers = params["num_lockers"]
    num_customers = params["num_customers"]

    L = range(num_lockers)
    C = range(num_customers)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if locker j is activated
    y = model.addVars(L, vtype=GRB.BINARY, name="y")
    # x[i,j] = 1 if customer i is assigned to locker j
    x = model.addVars(C, L, vtype=GRB.BINARY, name="x")

    # Objective: fixed costs + delivery costs
    model.setObjective(
        gp.quicksum(fixed_costs[j] * y[j] for j in L) +
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in C for j in L),
        GRB.MINIMIZE
    )

    # Each customer served by exactly one locker
    for i in C:
        model.addConstr(gp.quicksum(x[i, j] for j in L) == 1, name=f"single_source_{i}")

    # Capacity constraints
    for j in L:
        model.addConstr(
            gp.quicksum(demands[i] * x[i, j] for i in C) <= capacities[j] * y[j],
            name=f"capacity_{j}"
        )

    # Assignment only to active lockers
    for i in C:
        for j in L:
            model.addConstr(x[i, j] <= y[j], name=f"activation_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}