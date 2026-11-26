import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    n = len(demand)

    model = gp.Model("staffing")
    x = model.addVars(n, vtype=GRB.INTEGER, lb=0, obj=1, name="x")

    for t in range(n):
        model.addConstr(x[t] + x[(t - 1) % n] >= demand[t], name=f"cover_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    return {"objective": None, "status": "infeasible"}


if __name__ == "__main__":
    p = {"demand": [10, 15, 25, 20, 18, 12]}
    print(solve(p))