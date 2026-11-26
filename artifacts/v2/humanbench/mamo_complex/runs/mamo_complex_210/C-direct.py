import gurobipy as gp
from gurobipy import GRB

def solve(params):
    raw_material_cost_per_lb = params["raw_material_cost_per_lb"]
    lab_hours_per_lb_raw = params["lab_hours_per_lb_raw"]
    regular_brute_oz_per_lb = params["regular_brute_oz_per_lb"]
    regular_chanelle_oz_per_lb = params["regular_chanelle_oz_per_lb"]
    regular_brute_price_per_oz = params["regular_brute_price_per_oz"]
    regular_chanelle_price_per_oz = params["regular_chanelle_price_per_oz"]
    luxury_brute_price_per_oz = params["luxury_brute_price_per_oz"]
    luxury_chanelle_price_per_oz = params["luxury_chanelle_price_per_oz"]
    brute_further_lab_hours_per_oz = params["brute_further_lab_hours_per_oz"]
    chanelle_further_lab_hours_per_oz = params["chanelle_further_lab_hours_per_oz"]
    brute_further_cost_per_oz = params["brute_further_cost_per_oz"]
    chanelle_further_cost_per_oz = params["chanelle_further_cost_per_oz"]
    lab_hours_capacity = params["lab_hours_capacity"]
    raw_material_capacity_lb = params["raw_material_capacity_lb"]

    model = gp.Model("rylon_perfume")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x: pounds of raw material purchased and processed
    # rb: ounces of Regular Brute sold as Regular Brute
    # rc: ounces of Regular Chanelle sold as Regular Chanelle
    # lb_oz: ounces of Regular Brute further processed into Luxury Brute
    # lc_oz: ounces of Regular Chanelle further processed into Luxury Chanelle

    x = model.addVar(lb=0.0, name="raw_material_lbs")
    rb = model.addVar(lb=0.0, name="regular_brute_sold_oz")
    rc = model.addVar(lb=0.0, name="regular_chanelle_sold_oz")
    lb_oz = model.addVar(lb=0.0, name="luxury_brute_oz")
    lc_oz = model.addVar(lb=0.0, name="luxury_chanelle_oz")

    # Objective: maximize revenue minus raw material cost minus further processing costs
    # (lab hours cost is fixed, so excluded from optimization)
    revenue = (regular_brute_price_per_oz * rb
               + regular_chanelle_price_per_oz * rc
               + luxury_brute_price_per_oz * lb_oz
               + luxury_chanelle_price_per_oz * lc_oz)
    costs = (raw_material_cost_per_lb * x
             + brute_further_cost_per_oz * lb_oz
             + chanelle_further_cost_per_oz * lc_oz)
    model.setObjective(revenue - costs, GRB.MAXIMIZE)

    # Constraints

    # Raw material capacity
    model.addConstr(x <= raw_material_capacity_lb, name="raw_material_capacity")

    # Laboratory hours capacity:
    # Processing raw material uses lab_hours_per_lb_raw hours per lb
    # Further processing Brute uses brute_further_lab_hours_per_oz per oz
    # Further processing Chanelle uses chanelle_further_lab_hours_per_oz per oz
    model.addConstr(
        lab_hours_per_lb_raw * x
        + brute_further_lab_hours_per_oz * lb_oz
        + chanelle_further_lab_hours_per_oz * lc_oz
        <= lab_hours_capacity,
        name="lab_hours_capacity"
    )

    # Regular Brute availability: total Regular Brute produced = regular_brute_oz_per_lb * x
    # It can be sold as Regular Brute (rb) or further processed into Luxury Brute (lb_oz)
    model.addConstr(
        rb + lb_oz <= regular_brute_oz_per_lb * x,
        name="brute_balance"
    )

    # Regular Chanelle availability: total Regular Chanelle produced = regular_chanelle_oz_per_lb * x
    # It can be sold as Regular Chanelle (rc) or further processed into Luxury Chanelle (lc_oz)
    model.addConstr(
        rc + lc_oz <= regular_chanelle_oz_per_lb * x,
        name="chanelle_balance"
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