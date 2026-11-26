import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fiber_okra = params["fiber_okra"]
    fiber_carrots = params["fiber_carrots"]
    fiber_celery = params["fiber_celery"]
    fiber_cabbage = params["fiber_cabbage"]

    price_salmon = params["price_salmon"]
    price_beef = params["price_beef"]
    price_pork = params["price_pork"]
    price_okra = params["price_okra"]
    price_carrots = params["price_carrots"]
    price_celery = params["price_celery"]
    price_cabbage = params["price_cabbage"]

    budget = params["budget"]
    total_intake = params["total_intake"]
    min_protein_grams = params["min_protein_grams"]
    min_vegetable_grams = params["min_vegetable_grams"]

    model = gp.Model("mary_dinner")
    model.setParam("OutputFlag", 0)

    # Continuous variables: grams of each food
    salmon = model.addVar(lb=0.0, name="salmon")
    beef = model.addVar(lb=0.0, name="beef")
    pork = model.addVar(lb=0.0, name="pork")
    okra = model.addVar(lb=0.0, name="okra")
    carrots = model.addVar(lb=0.0, name="carrots")
    celery = model.addVar(lb=0.0, name="celery")
    cabbage = model.addVar(lb=0.0, name="cabbage")

    # Binary variables: which protein is chosen
    y_salmon = model.addVar(vtype=GRB.BINARY, name="y_salmon")
    y_beef = model.addVar(vtype=GRB.BINARY, name="y_beef")
    y_pork = model.addVar(vtype=GRB.BINARY, name="y_pork")

    # Binary variables: which vegetables are chosen
    y_okra = model.addVar(vtype=GRB.BINARY, name="y_okra")
    y_carrots = model.addVar(vtype=GRB.BINARY, name="y_carrots")
    y_celery = model.addVar(vtype=GRB.BINARY, name="y_celery")
    y_cabbage = model.addVar(vtype=GRB.BINARY, name="y_cabbage")

    # Objective: maximize fiber (fiber per 100g * grams / 100)
    model.setObjective(
        (fiber_okra * okra + fiber_carrots * carrots +
         fiber_celery * celery + fiber_cabbage * cabbage) / 100.0,
        GRB.MAXIMIZE
    )

    # Exactly one protein source
    model.addConstr(y_salmon + y_beef + y_pork == 1, name="one_protein")

    # At least two vegetables
    model.addConstr(y_okra + y_carrots + y_celery + y_cabbage >= 2, name="min_two_veg")

    # Big-M for linking protein quantities to binary selection
    # Total intake is an upper bound on any single food amount
    M = total_intake

    # Protein: if chosen, must take at least min_protein_grams; if not chosen, must be 0
    model.addConstr(salmon >= min_protein_grams * y_salmon, name="min_salmon")
    model.addConstr(salmon <= M * y_salmon, name="max_salmon")

    model.addConstr(beef >= min_protein_grams * y_beef, name="min_beef")
    model.addConstr(beef <= M * y_beef, name="max_beef")

    model.addConstr(pork >= min_protein_grams * y_pork, name="min_pork")
    model.addConstr(pork <= M * y_pork, name="max_pork")

    # Vegetables: if chosen, must take at least min_vegetable_grams; if not chosen, must be 0
    model.addConstr(okra >= min_vegetable_grams * y_okra, name="min_okra")
    model.addConstr(okra <= M * y_okra, name="max_okra")

    model.addConstr(carrots >= min_vegetable_grams * y_carrots, name="min_carrots")
    model.addConstr(carrots <= M * y_carrots, name="max_carrots")

    model.addConstr(celery >= min_vegetable_grams * y_celery, name="min_celery")
    model.addConstr(celery <= M * y_celery, name="max_celery")

    model.addConstr(cabbage >= min_vegetable_grams * y_cabbage, name="min_cabbage")
    model.addConstr(cabbage <= M * y_cabbage, name="max_cabbage")

    # Total intake constraint
    model.addConstr(
        salmon + beef + pork + okra + carrots + celery + cabbage == total_intake,
        name="total_intake"
    )

    # Budget constraint (prices are per 100g)
    model.addConstr(
        (price_salmon * salmon + price_beef * beef + price_pork * pork +
         price_okra * okra + price_carrots * carrots +
         price_celery * celery + price_cabbage * cabbage) / 100.0 <= budget,
        name="budget"
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