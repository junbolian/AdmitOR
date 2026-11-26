import gurobipy as gp
from gurobipy import GRB

def solve(params):
    mat_cost_A = params["mat_cost_A"]
    mat_cost_B = params["mat_cost_B"]
    mat_cost_C = params["mat_cost_C"]
    limit_A = params["limit_A"]
    limit_B = params["limit_B"]
    limit_C = params["limit_C"]
    proc_fee_A = params["proc_fee_A"]
    proc_fee_B = params["proc_fee_B"]
    proc_fee_C = params["proc_fee_C"]
    price_A = params["price_A"]
    price_B = params["price_B"]
    price_C = params["price_C"]
    content_A_in_A = params["content_A_in_A"]
    content_A_in_B = params["content_A_in_B"]
    content_C_in_A = params["content_C_in_A"]
    content_C_in_B = params["content_C_in_B"]
    content_C_in_C = params["content_C_in_C"]

    # Decision variables: x_A, x_B, x_C = kg of candy A, B, C produced per month
    model = gp.Model("candy_factory")
    model.setParam("OutputFlag", 0)

    x_A = model.addVar(lb=0.0, name="x_A")
    x_B = model.addVar(lb=0.0, name="x_B")
    x_C = model.addVar(lb=0.0, name="x_C")

    # Profit per kg of each candy:
    # Revenue - raw material cost - processing fee
    # Raw material cost per kg of candy:
    #   Candy A: content_A_in_A * mat_cost_A + (1 - content_A_in_A - content_C_in_A) * mat_cost_B + content_C_in_A * mat_cost_C
    #   Candy B: content_A_in_B * mat_cost_A + (1 - content_A_in_B - content_C_in_B) * mat_cost_B + content_C_in_B * mat_cost_C
    #   Candy C: (1 - content_C_in_C) * mat_cost_B + content_C_in_C * mat_cost_C
    # (Candy C contains no raw material A; remainder after C is raw material B)

    raw_cost_candyA = content_A_in_A * mat_cost_A + (1 - content_A_in_A - content_C_in_A) * mat_cost_B + content_C_in_A * mat_cost_C
    raw_cost_candyB = content_A_in_B * mat_cost_A + (1 - content_A_in_B - content_C_in_B) * mat_cost_B + content_C_in_B * mat_cost_C
    raw_cost_candyC = (1 - content_C_in_C) * mat_cost_B + content_C_in_C * mat_cost_C

    profit_A = price_A - raw_cost_candyA - proc_fee_A
    profit_B = price_B - raw_cost_candyB - proc_fee_B
    profit_C = price_C - raw_cost_candyC - proc_fee_C

    # Objective: maximize total profit
    model.setObjective(profit_A * x_A + profit_B * x_B + profit_C * x_C, GRB.MAXIMIZE)

    # Raw material usage constraints:
    # Raw material A usage: content_A_in_A * x_A + content_A_in_B * x_B <= limit_A
    model.addConstr(content_A_in_A * x_A + content_A_in_B * x_B <= limit_A, name="limit_raw_A")

    # Raw material B usage: (1-content_A_in_A-content_C_in_A)*x_A + (1-content_A_in_B-content_C_in_B)*x_B + (1-content_C_in_C)*x_C <= limit_B
    model.addConstr(
        (1 - content_A_in_A - content_C_in_A) * x_A
        + (1 - content_A_in_B - content_C_in_B) * x_B
        + (1 - content_C_in_C) * x_C <= limit_B,
        name="limit_raw_B"
    )

    # Raw material C usage: content_C_in_A * x_A + content_C_in_B * x_B + content_C_in_C * x_C <= limit_C
    model.addConstr(
        content_C_in_A * x_A + content_C_in_B * x_B + content_C_in_C * x_C <= limit_C,
        name="limit_raw_C"
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