import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_chicken    = params["protein_chicken"]
    cost_chicken       = params["cost_chicken"]
    protein_salmon     = params["protein_salmon"]
    cost_salmon        = params["cost_salmon"]
    protein_tofu       = params["protein_tofu"]
    cost_tofu          = params["cost_tofu"]
    protein_broccoli   = params["protein_broccoli"]
    cost_broccoli      = params["cost_broccoli"]
    protein_carrots    = params["protein_carrots"]
    cost_carrots       = params["cost_carrots"]
    protein_spinach    = params["protein_spinach"]
    cost_spinach       = params["cost_spinach"]
    protein_bell_pepper = params["protein_bell_pepper"]
    cost_bell_pepper   = params["cost_bell_pepper"]
    protein_mushrooms  = params["protein_mushrooms"]
    cost_mushrooms     = params["cost_mushrooms"]
    budget             = params["budget"]
    max_weight         = params["max_weight"]
    min_vegetable_types = params["min_vegetable_types"]

    model = gp.Model("mary_dinner")
    model.setParam("OutputFlag", 0)

    # Continuous variables for protein sources (units of 100g)
    chicken = model.addVar(lb=0.0, name="chicken")
    salmon  = model.addVar(lb=0.0, name="salmon")
    tofu    = model.addVar(lb=0.0, name="tofu")

    # Integer variables for vegetable packs (number of 100g packs)
    broccoli    = model.addVar(lb=0, vtype=GRB.INTEGER, name="broccoli")
    carrots     = model.addVar(lb=0, vtype=GRB.INTEGER, name="carrots")
    spinach     = model.addVar(lb=0, vtype=GRB.INTEGER, name="spinach")
    bell_pepper = model.addVar(lb=0, vtype=GRB.INTEGER, name="bell_pepper")
    mushrooms   = model.addVar(lb=0, vtype=GRB.INTEGER, name="mushrooms")

    # Binary variables indicating whether each vegetable type is selected
    y_broccoli    = model.addVar(vtype=GRB.BINARY, name="y_broccoli")
    y_carrots     = model.addVar(vtype=GRB.BINARY, name="y_carrots")
    y_spinach     = model.addVar(vtype=GRB.BINARY, name="y_spinach")
    y_bell_pepper = model.addVar(vtype=GRB.BINARY, name="y_bell_pepper")
    y_mushrooms   = model.addVar(vtype=GRB.BINARY, name="y_mushrooms")

    # Big-M for vegetable pack counts (at most max_weight/100 packs of any single veg)
    big_m = max_weight / 100.0

    # Link binary selection to pack counts
    model.addConstr(broccoli    <= big_m * y_broccoli,    name="link_broccoli")
    model.addConstr(carrots     <= big_m * y_carrots,     name="link_carrots")
    model.addConstr(spinach     <= big_m * y_spinach,     name="link_spinach")
    model.addConstr(bell_pepper <= big_m * y_bell_pepper, name="link_bell_pepper")
    model.addConstr(mushrooms   <= big_m * y_mushrooms,   name="link_mushrooms")

    # At least min_vegetable_types different vegetable types
    model.addConstr(
        y_broccoli + y_carrots + y_spinach + y_bell_pepper + y_mushrooms >= min_vegetable_types,
        name="min_veg_types"
    )

    # Budget constraint (all quantities are in units of 100g, costs are per 100g)
    model.addConstr(
        cost_chicken * chicken
        + cost_salmon * salmon
        + cost_tofu * tofu
        + cost_broccoli * broccoli
        + cost_carrots * carrots
        + cost_spinach * spinach
        + cost_bell_pepper * bell_pepper
        + cost_mushrooms * mushrooms
        <= budget,
        name="budget"
    )

    # Weight constraint (each unit = 100g)
    model.addConstr(
        100.0 * chicken
        + 100.0 * salmon
        + 100.0 * tofu
        + 100.0 * broccoli
        + 100.0 * carrots
        + 100.0 * spinach
        + 100.0 * bell_pepper
        + 100.0 * mushrooms
        <= max_weight,
        name="max_weight"
    )

    # Objective: maximize total protein
    model.setObjective(
        protein_chicken * chicken
        + protein_salmon * salmon
        + protein_tofu * tofu
        + protein_broccoli * broccoli
        + protein_carrots * carrots
        + protein_spinach * spinach
        + protein_bell_pepper * bell_pepper
        + protein_mushrooms * mushrooms,
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}