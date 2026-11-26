import gurobipy as gp
from gurobipy import GRB

def solve(params):
    raw_material_cost_per_lb = params["raw_material_cost_per_lb"]
    lab_hours_per_lb_processing = params["lab_hours_per_lb_processing"]
    brute_oz_per_lb = params["brute_oz_per_lb"]
    chanelle_oz_per_lb = params["chanelle_oz_per_lb"]
    regular_brute_price_per_oz = params["regular_brute_price_per_oz"]
    regular_chanelle_price_per_oz = params["regular_chanelle_price_per_oz"]
    luxury_brute_price_per_oz = params["luxury_brute_price_per_oz"]
    luxury_chanelle_price_per_oz = params["luxury_chanelle_price_per_oz"]
    luxury_brute_lab_hours_per_oz = params["luxury_brute_lab_hours_per_oz"]
    luxury_chanelle_lab_hours_per_oz = params["luxury_chanelle_lab_hours_per_oz"]
    luxury_brute_cost_per_oz = params["luxury_brute_cost_per_oz"]
    luxury_chanelle_cost_per_oz = params["luxury_chanelle_cost_per_oz"]
    lab_hours_capacity = params["lab_hours_capacity"]
    raw_material_capacity_lb = params["raw_material_capacity_lb"]

    model = gp.Model("rylon_perfume")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x: pounds of raw material purchased and processed
    x = model.addVar(lb=0.0, name="raw_material_lb")

    # lb: ounces of Regular Brute further processed into Luxury Brute
    lb_var = model.addVar(lb=0.0, name="luxury_brute_oz")

    # lc: ounces of Regular Chanelle further processed into Luxury Chanelle
    lc_var = model.addVar(lb=0.0, name="luxury_chanelle_oz")

    # Regular Brute sold = total Regular Brute produced - amount further processed
    # Regular Chanelle sold = total Regular Chanelle produced - amount further processed
    # Total Regular Brute produced = brute_oz_per_lb * x
    # Total Regular Chanelle produced = chanelle_oz_per_lb * x

    # Objective: maximize profit
    # Revenue from Regular Brute sold: regular_brute_price_per_oz * (brute_oz_per_lb * x - lb_var)
    # Revenue from Regular Chanelle sold: regular_chanelle_price_per_oz * (chanelle_oz_per_lb * x - lc_var)
    # Revenue from Luxury Brute: luxury_brute_price_per_oz * lb_var
    # Revenue from Luxury Chanelle: luxury_chanelle_price_per_oz * lc_var
    # Costs: raw material cost + luxury processing costs
    # Raw material cost: raw_material_cost_per_lb * x
    # Luxury Brute processing cost: luxury_brute_cost_per_oz * lb_var
    # Luxury Chanelle processing cost: luxury_chanelle_cost_per_oz * lc_var
    # Lab hours are fixed cost (not subtracted from profit per problem statement)

    profit = (
        regular_brute_price_per_oz * (brute_oz_per_lb * x - lb_var)
        + regular_chanelle_price_per_oz * (chanelle_oz_per_lb * x - lc_var)
        + luxury_brute_price_per_oz * lb_var
        + luxury_chanelle_price_per_oz * lc_var
        - raw_material_cost_per_lb * x
        - luxury_brute_cost_per_oz * lb_var
        - luxury_chanelle_cost_per_oz * lc_var
    )

    model.setObjective(profit, GRB.MAXIMIZE)

    # Constraints

    # Lab hours: processing raw material + further processing luxury products
    model.addConstr(
        lab_hours_per_lb_processing * x
        + luxury_brute_lab_hours_per_oz * lb_var
        + luxury_chanelle_lab_hours_per_oz * lc_var
        <= lab_hours_capacity,
        name="lab_hours"
    )

    # Raw material capacity
    model.addConstr(x <= raw_material_capacity_lb, name="raw_material_cap")

    # Cannot further process more Regular Brute than produced
    model.addConstr(lb_var <= brute_oz_per_lb * x, name="brute_balance")

    # Cannot further process more Regular Chanelle than produced
    model.addConstr(lc_var <= chanelle_oz_per_lb * x, name="chanelle_balance")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}