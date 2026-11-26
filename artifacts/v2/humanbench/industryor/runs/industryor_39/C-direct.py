import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken = params["protein_chicken"]
    protein_salmon  = params["protein_salmon"]
    protein_tofu    = params["protein_tofu"]
    price_chicken   = params["price_chicken"]
    price_salmon    = params["price_salmon"]
    price_tofu      = params["price_tofu"]
    budget          = params["budget"]
    max_weight      = params["max_weight"]

    model = gp.Model("dinner_protein")
    model.setParam("OutputFlag", 0)

    # Decision variables: grams (in units of 100g) of each protein source
    x_chicken = model.addVar(lb=0.0, name="x_chicken")
    x_salmon  = model.addVar(lb=0.0, name="x_salmon")
    x_tofu    = model.addVar(lb=0.0, name="x_tofu")

    # Binary variables indicating whether each protein source is used
    y_chicken = model.addVar(vtype=GRB.BINARY, name="y_chicken")
    y_salmon  = model.addVar(vtype=GRB.BINARY, name="y_salmon")
    y_tofu    = model.addVar(vtype=GRB.BINARY, name="y_tofu")

    # Objective: maximize total protein (grams)
    model.setObjective(
        protein_chicken * x_chicken + protein_salmon * x_salmon + protein_tofu * x_tofu,
        GRB.MAXIMIZE
    )

    # Budget constraint (prices are per 100g, variables are in 100g units)
    model.addConstr(
        price_chicken * x_chicken + price_salmon * x_salmon + price_tofu * x_tofu <= budget,
        "budget"
    )

    # Weight constraint (max_weight is in grams; x variables are in 100g units)
    model.addConstr(
        100.0 * (x_chicken + x_salmon + x_tofu) <= max_weight,
        "max_weight"
    )

    # At least one protein source must be chosen
    model.addConstr(y_chicken + y_salmon + y_tofu >= 1, "min_protein_sources")

    # Big-M linking: if y_i = 0, x_i must be 0
    big_m = max(budget / price_chicken, budget / price_salmon, budget / price_tofu,
                max_weight / 100.0)
    model.addConstr(x_chicken <= big_m * y_chicken, "link_chicken")
    model.addConstr(x_salmon  <= big_m * y_salmon,  "link_salmon")
    model.addConstr(x_tofu    <= big_m * y_tofu,    "link_tofu")

    # If a protein source is chosen, it must have positive amount (epsilon = 0.01 units = 1g)
    epsilon = 0.01
    model.addConstr(x_chicken >= epsilon * y_chicken, "min_chicken")
    model.addConstr(x_salmon  >= epsilon * y_salmon,  "min_salmon")
    model.addConstr(x_tofu    >= epsilon * y_tofu,    "min_tofu")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}