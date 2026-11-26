import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_I        = params["supply_I"]
    supply_I_prime  = params["supply_I_prime"]
    supply_II       = params["supply_II"]
    cost_I          = params["cost_I"]
    cost_I_prime    = params["cost_I_prime"]
    cost_II         = params["cost_II"]
    price_red       = params["price_red"]
    price_yellow    = params["price_yellow"]
    price_blue      = params["price_blue"]
    red_min_output          = params["red_min_output"]
    red_gradeI_upper_frac   = params["red_gradeI_upper_frac"]
    red_gradeI_lower_frac   = params["red_gradeI_lower_frac"]
    yellow_gradeII_upper_frac = params["yellow_gradeII_upper_frac"]
    yellow_gradeI_lower_frac  = params["yellow_gradeI_lower_frac"]
    blue_gradeI_upper_frac  = params["blue_gradeI_upper_frac"]
    blue_gradeI_lower_frac  = params["blue_gradeI_lower_frac"]

    # sources: 0=grade I (cost_I), 1=grade I' (cost_I_prime), 2=grade II (cost_II)
    # brands:  0=red, 1=yellow, 2=blue
    sources = [0, 1, 2]
    brands  = [0, 1, 2]

    model = gp.Model("wine_blending")
    model.setParam("OutputFlag", 0)

    # x[s, b] = kg of source s used in brand b
    x = model.addVars(sources, brands, lb=0.0, name="x")

    # Total output of each brand
    total_red    = x[0,0] + x[1,0] + x[2,0]
    total_yellow = x[0,1] + x[1,1] + x[2,1]
    total_blue   = x[0,2] + x[1,2] + x[2,2]

    # Supply constraints
    model.addConstr(x[0,0] + x[0,1] + x[0,2] <= supply_I,       name="supply_gradeI")
    model.addConstr(x[1,0] + x[1,1] + x[1,2] <= supply_I_prime, name="supply_gradeI_prime")
    model.addConstr(x[2,0] + x[2,1] + x[2,2] <= supply_II,      name="supply_gradeII")

    # Minimum red brand production
    model.addConstr(total_red >= red_min_output, name="red_min")

    # Red brand blending constraints:
    #   grade I (first row, cost_I)  < red_gradeI_upper_frac * total_red
    #   grade I'(second row, cost_I_prime) > red_gradeI_lower_frac * total_red
    model.addConstr(x[0,0] <= red_gradeI_upper_frac * total_red, name="red_I_upper")
    model.addConstr(x[1,0] >= red_gradeI_lower_frac * total_red, name="red_I_prime_lower")

    # Yellow brand blending constraints:
    #   grade II < yellow_gradeII_upper_frac * total_yellow
    #   grade I' > yellow_gradeI_lower_frac * total_yellow
    model.addConstr(x[2,1] <= yellow_gradeII_upper_frac * total_yellow, name="yellow_II_upper")
    model.addConstr(x[1,1] >= yellow_gradeI_lower_frac  * total_yellow, name="yellow_I_prime_lower")

    # Blue brand blending constraints:
    #   grade I (first row) < blue_gradeI_upper_frac * total_blue
    #   grade I'(second row) > blue_gradeI_lower_frac * total_blue
    model.addConstr(x[0,2] <= blue_gradeI_upper_frac * total_blue, name="blue_I_upper")
    model.addConstr(x[1,2] >= blue_gradeI_lower_frac * total_blue, name="blue_I_prime_lower")

    # Objective: maximize profit = revenue - cost
    revenue = (price_red    * total_red
             + price_yellow * total_yellow
             + price_blue   * total_blue)

    cost = (cost_I       * (x[0,0] + x[0,1] + x[0,2])
          + cost_I_prime * (x[1,0] + x[1,1] + x[1,2])
          + cost_II      * (x[2,0] + x[2,1] + x[2,2]))

    model.setObjective(revenue - cost, GRB.MAXIMIZE)

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