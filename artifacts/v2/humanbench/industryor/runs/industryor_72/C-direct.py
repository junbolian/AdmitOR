import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_apples = params["profit_apples"]
    profit_pears = params["profit_pears"]
    profit_oranges = params["profit_oranges"]
    profit_lemons = params["profit_lemons"]
    total_land = params["total_land"]
    apples_vs_pears_ratio = params["apples_vs_pears_ratio"]
    apples_vs_lemons_ratio = params["apples_vs_lemons_ratio"]
    oranges_vs_lemons_ratio = params["oranges_vs_lemons_ratio"]
    max_fruit_types = params["max_fruit_types"]

    model = gp.Model("farm_optimization")
    model.setParam("OutputFlag", 0)

    # Continuous variables for acres of each fruit
    x_apples = model.addVar(lb=0.0, name="x_apples")
    x_pears = model.addVar(lb=0.0, name="x_pears")
    x_oranges = model.addVar(lb=0.0, name="x_oranges")
    x_lemons = model.addVar(lb=0.0, name="x_lemons")

    # Binary variables indicating whether each fruit type is grown
    y_apples = model.addVar(vtype=GRB.BINARY, name="y_apples")
    y_pears = model.addVar(vtype=GRB.BINARY, name="y_pears")
    y_oranges = model.addVar(vtype=GRB.BINARY, name="y_oranges")
    y_lemons = model.addVar(vtype=GRB.BINARY, name="y_lemons")

    # Objective: maximize profit
    model.setObjective(
        profit_apples * x_apples + profit_pears * x_pears +
        profit_oranges * x_oranges + profit_lemons * x_lemons,
        GRB.MAXIMIZE
    )

    # Total land constraint
    model.addConstr(x_apples + x_pears + x_oranges + x_lemons <= total_land, "total_land")

    # Ratio constraints (only binding when relevant fruits are grown)
    # apples >= apples_vs_pears_ratio * pears
    model.addConstr(x_apples >= apples_vs_pears_ratio * x_pears, "apples_vs_pears")

    # apples >= apples_vs_lemons_ratio * lemons
    model.addConstr(x_apples >= apples_vs_lemons_ratio * x_lemons, "apples_vs_lemons")

    # oranges == oranges_vs_lemons_ratio * lemons
    model.addConstr(x_oranges == oranges_vs_lemons_ratio * x_lemons, "oranges_vs_lemons")

    # Maximum number of fruit types
    model.addConstr(y_apples + y_pears + y_oranges + y_lemons <= max_fruit_types, "max_types")

    # Big-M linking constraints: if y_i = 0, x_i must be 0
    M = total_land
    model.addConstr(x_apples <= M * y_apples, "link_apples")
    model.addConstr(x_pears <= M * y_pears, "link_pears")
    model.addConstr(x_oranges <= M * y_oranges, "link_oranges")
    model.addConstr(x_lemons <= M * y_lemons, "link_lemons")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}