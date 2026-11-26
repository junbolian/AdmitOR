import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    capacity_A = params["capacity_A"]
    capacity_B = params["capacity_B"]
    capacity_C = params["capacity_C"]
    min_chairs = params["min_chairs"]
    max_chairs = params["max_chairs"]
    min_B_if_A = params["min_B_if_A"]

    model = gp.Model("furniture_chairs")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of orders from each manufacturer (integer)
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")
    x_C = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_C")

    # Binary indicators: whether any orders are placed with each manufacturer
    y_A = model.addVar(vtype=GRB.BINARY, name="y_A")
    y_B = model.addVar(vtype=GRB.BINARY, name="y_B")

    model.update()

    # Objective: minimize total cost
    # Total chairs = capacity_A * x_A + capacity_B * x_B + capacity_C * x_C
    # Total cost = cost_A * (capacity_A * x_A) + cost_B * (capacity_B * x_B) + cost_C * (capacity_C * x_C)
    model.setObjective(
        cost_A * capacity_A * x_A + cost_B * capacity_B * x_B + cost_C * capacity_C * x_C,
        GRB.MINIMIZE
    )

    # Total chairs constraints
    total_chairs = capacity_A * x_A + capacity_B * x_B + capacity_C * x_C
    model.addConstr(total_chairs >= min_chairs, name="min_chairs")
    model.addConstr(total_chairs <= max_chairs, name="max_chairs")

    # Big-M for linking x_A to y_A and x_B to y_B
    # Upper bound on orders: max_chairs is a safe big-M divisor
    M_A = max_chairs  # x_A <= M_A * y_A (since capacity_A * x_A <= max_chairs => x_A <= max_chairs)
    M_B = max_chairs

    # y_A = 1 iff x_A >= 1
    model.addConstr(x_A <= M_A * y_A, name="link_xA_yA_upper")
    model.addConstr(x_A >= y_A, name="link_xA_yA_lower")

    # y_B = 1 iff x_B >= 1
    model.addConstr(x_B <= M_B * y_B, name="link_xB_yB_upper")
    model.addConstr(x_B >= y_B, name="link_xB_yB_lower")

    # If A is ordered (y_A = 1), must order at least min_B_if_A chairs from B
    # capacity_B * x_B >= min_B_if_A * y_A
    model.addConstr(capacity_B * x_B >= min_B_if_A * y_A, name="min_B_if_A")

    # If B is ordered (y_B = 1), must order from C (x_C >= 1)
    model.addConstr(x_C >= y_B, name="C_if_B")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {status}"}