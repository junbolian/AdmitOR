import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a_proc1_hours = params["a_proc1_hours"]
    a_proc2_hours = params["a_proc2_hours"]
    b_proc1_hours = params["b_proc1_hours"]
    b_proc2_hours = params["b_proc2_hours"]
    proc1_capacity = params["proc1_capacity"]
    proc2_capacity = params["proc2_capacity"]
    byproduct_per_b = params["byproduct_per_b"]
    c_sales_limit = params["c_sales_limit"]
    c_disposal_cost = params["c_disposal_cost"]
    a_profit = params["a_profit"]
    b_profit = params["b_profit"]
    c_sell_profit = params["c_sell_profit"]

    model = gp.Model("production_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x_a = model.addVar(lb=0.0, name="x_a")          # units of product A
    x_b = model.addVar(lb=0.0, name="x_b")          # units of product B
    c_sold = model.addVar(lb=0.0, name="c_sold")     # units of by-product C sold
    c_disposed = model.addVar(lb=0.0, name="c_disposed")  # units of by-product C disposed

    # Objective: maximize total profit
    model.setObjective(
        a_profit * x_a + b_profit * x_b + c_sell_profit * c_sold - c_disposal_cost * c_disposed,
        GRB.MAXIMIZE
    )

    # Process capacity constraints
    model.addConstr(a_proc1_hours * x_a + b_proc1_hours * x_b <= proc1_capacity, name="proc1_capacity")
    model.addConstr(a_proc2_hours * x_a + b_proc2_hours * x_b <= proc2_capacity, name="proc2_capacity")

    # By-product C balance: total C generated = sold + disposed
    model.addConstr(byproduct_per_b * x_b == c_sold + c_disposed, name="c_balance")

    # Sales limit for by-product C
    model.addConstr(c_sold <= c_sales_limit, name="c_sales_limit")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}