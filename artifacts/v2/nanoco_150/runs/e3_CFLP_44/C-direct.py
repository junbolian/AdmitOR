import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # list of 5 values
    capacity = params["capacity"]          # list of 5 values
    demand = params["demand"]              # list of 19 values
    logistics_cost = params["logistics_cost"]  # 19x5 matrix

    num_facilities = 5
    num_clients = 19
    facilities = range(num_facilities)
    clients = range(num_clients)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if facility j is opened
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")

    # x[i,j] = 1 if client i is assigned to facility j
    x = model.addVars(clients, facilities, vtype=GRB.BINARY, name="x")

    # Objective: minimize fixed costs + logistics costs
    model.setObjective(
        gp.quicksum(fixed_cost[j] * y[j] for j in facilities) +
        gp.quicksum(logistics_cost[i][j] * x[i, j] for i in clients for j in facilities),
        GRB.MINIMIZE
    )

    # Each client assigned to exactly one facility
    for i in clients:
        model.addConstr(gp.quicksum(x[i, j] for j in facilities) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in facilities:
        model.addConstr(
            gp.quicksum(demand[i] * x[i, j] for i in clients) <= capacity[j] * y[j],
            name=f"cap_{j}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}