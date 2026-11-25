import gurobipy as gp
from gurobipy import GRB

def solve(params):
    value = params["value"]
    weight = params["weight"]
    capacity = params["capacity"]
    num_packages = params["num_packages"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_packages, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(value[i] * x[i] for i in range(num_packages)), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(weight[i] * x[i] for i in range(num_packages)) <= capacity,
        name="weight_capacity"
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