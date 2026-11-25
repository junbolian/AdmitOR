import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]
    leg_utilization = params["leg_utilization"]

    n_legs = len(capacity)
    n_packages = len(revenue)

    model = gp.Model("airline_revenue")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_packages, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(revenue[j] * x[j] for j in range(n_packages)), GRB.MAXIMIZE)

    for j in range(n_packages):
        model.addConstr(x[j] <= demand[j], name=f"demand_{j}")

    for i in range(n_legs):
        model.addConstr(
            gp.quicksum(leg_utilization[i][j] * x[j] for j in range(n_packages)) <= capacity[i],
            name=f"capacity_{i}"
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