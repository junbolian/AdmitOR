import gurobipy as gp
from gurobipy import GRB

def solve(params):
    value_A = params["value_A"]
    value_B = params["value_B"]
    value_C = params["value_C"]
    weight_A = params["weight_A"]
    weight_B = params["weight_B"]
    weight_C = params["weight_C"]
    capacity = params["capacity"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_A = model.addVar(vtype=GRB.BINARY, name="x_A")
    x_B = model.addVar(vtype=GRB.BINARY, name="x_B")
    x_C = model.addVar(vtype=GRB.BINARY, name="x_C")

    model.setObjective(value_A * x_A + value_B * x_B + value_C * x_C, GRB.MAXIMIZE)

    model.addConstr(weight_A * x_A + weight_B * x_B + weight_C * x_C <= capacity, name="weight_capacity")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}