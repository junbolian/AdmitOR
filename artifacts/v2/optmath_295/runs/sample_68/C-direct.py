import gurobipy as gp
from gurobipy import GRB

def solve(params):
    vehicle_cost_1 = params["vehicle_cost_1"]
    vehicle_cost_2 = params["vehicle_cost_2"]
    vehicle_cost_3 = params["vehicle_cost_3"]
    vehicle_cost_4 = params["vehicle_cost_4"]
    vehicle_cost_5 = params["vehicle_cost_5"]
    vehicle_cost_6 = params["vehicle_cost_6"]

    model = gp.Model("vehicle_deployment")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy vehicle i or not
    x1 = model.addVar(vtype=GRB.BINARY, name="x1")
    x2 = model.addVar(vtype=GRB.BINARY, name="x2")
    x3 = model.addVar(vtype=GRB.BINARY, name="x3")
    x4 = model.addVar(vtype=GRB.BINARY, name="x4")
    x5 = model.addVar(vtype=GRB.BINARY, name="x5")
    x6 = model.addVar(vtype=GRB.BINARY, name="x6")

    # Objective: minimize total deployment cost
    model.setObjective(
        vehicle_cost_1 * x1 + vehicle_cost_2 * x2 + vehicle_cost_3 * x3 +
        vehicle_cost_4 * x4 + vehicle_cost_5 * x5 + vehicle_cost_6 * x6,
        GRB.MINIMIZE
    )

    # Route coverage constraints
    model.addConstr(x6 >= 1, name="route1")
    model.addConstr(x2 + x4 + x6 >= 1, name="route2")
    model.addConstr(x1 + x3 + x4 >= 1, name="route3")
    model.addConstr(x3 >= 1, name="route4")
    model.addConstr(x1 + x5 + x6 >= 1, name="route5")
    model.addConstr(x1 + x4 >= 1, name="route6")
    model.addConstr(x3 + x5 >= 1, name="route7")
    model.addConstr(x4 >= 1, name="route8")
    model.addConstr(x3 + x5 + x6 >= 1, name="route9")
    model.addConstr(x4 + x5 + x6 >= 1, name="route10")
    model.addConstr(x3 + x4 >= 1, name="route11")
    model.addConstr(x1 + x3 + x5 + x6 >= 1, name="route12")
    model.addConstr(x3 + x4 + x6 >= 1, name="route13")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}