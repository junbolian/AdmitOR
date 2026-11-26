import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    num_facilities = len(supply)
    num_centers = len(demand)

    model = gp.Model()
    model.Params.OutputFlag = 0

    x = model.addVars(num_facilities, num_centers, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_facilities) for j in range(num_centers)),
        GRB.MINIMIZE
    )

    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_centers)) == supply[i],
            name=f"supply_{i}"
        )

    for j in range(num_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demand[j],
            name=f"demand_{j}"
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