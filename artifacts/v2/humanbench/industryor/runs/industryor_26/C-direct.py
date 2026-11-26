import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a_front_hours   = params["a_front_hours"]
    b_front_hours   = params["b_front_hours"]
    a_back_hours    = params["a_back_hours"]
    b_back_hours    = params["b_back_hours"]
    front_capacity  = params["front_capacity"]
    back_capacity   = params["back_capacity"]
    c_per_b         = params["c_per_b"]
    c_sellable_max  = params["c_sellable_max"]
    c_disposal_cost = params["c_disposal_cost"]
    profit_a        = params["profit_a"]
    profit_b        = params["profit_b"]
    profit_c        = params["profit_c"]

    model = gp.Model("production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x_a   = model.addVar(lb=0, name="x_a")          # units of product A
    x_b   = model.addVar(lb=0, name="x_b")          # units of product B
    c_sell = model.addVar(lb=0, name="c_sell")       # units of byproduct C sold
    c_disp = model.addVar(lb=0, name="c_disp")       # units of byproduct C disposed

    # Objective: maximize profit
    model.setObjective(
        profit_a * x_a + profit_b * x_b + profit_c * c_sell - c_disposal_cost * c_disp,
        GRB.MAXIMIZE
    )

    # Constraints
    model.addConstr(a_front_hours * x_a + b_front_hours * x_b <= front_capacity, "front_capacity")
    model.addConstr(a_back_hours  * x_a + b_back_hours  * x_b <= back_capacity,  "back_capacity")

    # Byproduct C balance: total C generated = sold + disposed
    model.addConstr(c_per_b * x_b == c_sell + c_disp, "c_balance")

    # Selling limit for C
    model.addConstr(c_sell <= c_sellable_max, "c_sell_limit")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}