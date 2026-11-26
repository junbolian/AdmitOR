import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_apples = params["profit_apples"]
    profit_pears = params["profit_pears"]
    profit_oranges = params["profit_oranges"]
    profit_lemons = params["profit_lemons"]
    total_land = params["total_land"]
    apple_vs_pear_ratio = params["apple_vs_pear_ratio"]
    apple_vs_lemon_ratio = params["apple_vs_lemon_ratio"]
    orange_vs_lemon_ratio = params["orange_vs_lemon_ratio"]
    max_fruit_types = params["max_fruit_types"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Continuous acres for each fruit
    x_a = model.addVar(lb=0, name="x_apples")
    x_p = model.addVar(lb=0, name="x_pears")
    x_o = model.addVar(lb=0, name="x_oranges")
    x_l = model.addVar(lb=0, name="x_lemons")

    # Binary variables: whether each fruit type is grown
    y_a = model.addVar(vtype=GRB.BINARY, name="y_apples")
    y_p = model.addVar(vtype=GRB.BINARY, name="y_pears")
    y_o = model.addVar(vtype=GRB.BINARY, name="y_oranges")
    y_l = model.addVar(vtype=GRB.BINARY, name="y_lemons")

    # Objective: maximize profit
    model.setObjective(
        profit_apples * x_a + profit_pears * x_p + profit_oranges * x_o + profit_lemons * x_l,
        GRB.MAXIMIZE
    )

    # Total land constraint
    model.addConstr(x_a + x_p + x_o + x_l <= total_land, name="total_land")

    # Big-M for linking acres to binary (use total_land as big-M)
    M = total_land

    # If a fruit is not grown, its acreage must be 0
    model.addConstr(x_a <= M * y_a, name="link_apples")
    model.addConstr(x_p <= M * y_p, name="link_pears")
    model.addConstr(x_o <= M * y_o, name="link_oranges")
    model.addConstr(x_l <= M * y_l, name="link_lemons")

    # At most max_fruit_types types grown
    model.addConstr(y_a + y_p + y_o + y_l <= max_fruit_types, name="max_types")

    # Apple vs pear ratio: x_a >= apple_vs_pear_ratio * x_p
    model.addConstr(x_a >= apple_vs_pear_ratio * x_p, name="apple_pear_ratio")

    # Apple vs lemon ratio: x_a >= apple_vs_lemon_ratio * x_l
    model.addConstr(x_a >= apple_vs_lemon_ratio * x_l, name="apple_lemon_ratio")

    # Orange vs lemon ratio (conditional on lemons grown):
    # If y_l = 1: x_o = orange_vs_lemon_ratio * x_l
    # If y_l = 0: no constraint on this relationship
    # Encode: x_o >= orange_vs_lemon_ratio * x_l (always valid since x_l=0 when y_l=0)
    # and x_o <= orange_vs_lemon_ratio * x_l + M * (1 - y_l)
    model.addConstr(x_o >= orange_vs_lemon_ratio * x_l, name="orange_lemon_lb")
    model.addConstr(x_o <= orange_vs_lemon_ratio * x_l + M * (1 - y_l), name="orange_lemon_ub")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}