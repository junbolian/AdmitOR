import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]  # list of 6 values indexed 0..5

    # Time blocks (4-hour each, in order):
    # 0: 2-6, 1: 6-10, 2: 10-14, 3: 14-18, 4: 18-22, 5: 22-2
    # Waiters start at the beginning of each 4-hour block and work 8 hours (2 consecutive blocks).
    # x[i] = number of waiters starting their shift at block i.
    # A waiter starting at block i covers blocks i and (i+1) mod 6.

    model = gp.Model("waiter_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i] >= 0 integer, number of waiters starting at block i
    x = model.addVars(6, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total waiters
    model.setObjective(gp.quicksum(x[i] for i in range(6)), GRB.MINIMIZE)

    # Coverage constraints: for each block j, sum of waiters covering it >= demand[j]
    # Block j is covered by shifts starting at j and (j-1) mod 6
    for j in range(6):
        model.addConstr(
            x[j] + x[(j - 1) % 6] >= demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}