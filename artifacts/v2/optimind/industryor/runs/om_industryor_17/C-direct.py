import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    chairs_per_order_A = params["chairs_per_order_A"]
    chairs_per_order_B = params["chairs_per_order_B"]
    chairs_per_order_C = params["chairs_per_order_C"]
    min_chairs = params["min_chairs"]
    max_chairs = params["max_chairs"]
    min_B_if_A = params["min_B_if_A"]

    model = gp.Model("furniture_store")
    model.setParam("OutputFlag", 0)

    # Number of orders from each manufacturer (integer, non-negative)
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")
    x_C = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_C")

    # Binary indicators: y_A = 1 if A is used, y_B = 1 if B is used
    y_A = model.addVar(vtype=GRB.BINARY, name="y_A")
    y_B = model.addVar(vtype=GRB.BINARY, name="y_B")
    y_C = model.addVar(vtype=GRB.BINARY, name="y_C")

    # Total chairs
    total_chairs = chairs_per_order_A * x_A + chairs_per_order_B * x_B + chairs_per_order_C * x_C

    # Objective: minimize total cost
    model.setObjective(
        cost_A * chairs_per_order_A * x_A +
        cost_B * chairs_per_order_B * x_B +
        cost_C * chairs_per_order_C * x_C,
        GRB.MINIMIZE
    )

    # Chair bounds
    model.addConstr(total_chairs >= min_chairs, name="min_chairs")
    model.addConstr(total_chairs <= max_chairs, name="max_chairs")

    # Big-M for linking x to y (upper bound: max_chairs / min chairs_per_order gives max orders)
    M = max_chairs  # safe upper bound on number of orders

    # y_A = 1 iff x_A >= 1
    model.addConstr(x_A <= M * y_A, name="link_yA_upper")
    model.addConstr(x_A >= y_A, name="link_yA_lower")

    # y_B = 1 iff x_B >= 1
    model.addConstr(x_B <= M * y_B, name="link_yB_upper")
    model.addConstr(x_B >= y_B, name="link_yB_lower")

    # y_C = 1 iff x_C >= 1
    model.addConstr(x_C <= M * y_C, name="link_yC_upper")
    model.addConstr(x_C >= y_C, name="link_yC_lower")

    # If A is used, must order at least min_B_if_A chairs from B
    # chairs_per_order_B * x_B >= min_B_if_A * y_A
    model.addConstr(
        chairs_per_order_B * x_B >= min_B_if_A * y_A,
        name="min_B_if_A_used"
    )

    # If B is used, must also order from C (y_C >= y_B)
    model.addConstr(y_C >= y_B, name="C_if_B_used")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}