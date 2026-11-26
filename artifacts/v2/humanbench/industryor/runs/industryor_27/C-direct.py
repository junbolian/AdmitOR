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
    total_food = params["total_food"]
    min_vegetables = params["min_vegetables"]

    model = gp.Model("mary_dinner")
    model.setParam("OutputFlag", 0)

    # Continuous variables: grams (in units of 100g) of each food
    salmon = model.addVar(lb=0.0, name="salmon")
    beef = model.addVar(lb=0.0, name="beef")
    pork = model.addVar(lb=0.0, name="pork")
    okra = model.addVar(lb=0.0, name="okra")
    carrots = model.addVar(lb=0.0, name="carrots")
    celery = model.addVar(lb=0.0, name="celery")
    cabbage = model.addVar(lb=0.0, name="cabbage")

    # Binary variables: select exactly one protein
    y_salmon = model.addVar(vtype=GRB.BINARY, name="y_salmon")
    y_beef = model.addVar(vtype=GRB.BINARY, name="y_beef")
    y_pork = model.addVar(vtype=GRB.BINARY, name="y_pork")

    # Binary variables: select which vegetables are used
    z_okra = model.addVar(vtype=GRB.BINARY, name="z_okra")
    z_carrots = model.addVar(vtype=GRB.BINARY, name="z_carrots")
    z_celery = model.addVar(vtype=GRB.BINARY, name="z_celery")
    z_cabbage = model.addVar(vtype=GRB.BINARY, name="z_cabbage")

    model.update()

    # Objective: maximize fiber intake (fiber per 100g * quantity in 100g units)
    model.setObjective(
        fiber_okra * okra + fiber_carrots * carrots +
        fiber_celery * celery + fiber_cabbage * cabbage,
        GRB.MAXIMIZE
    )

    # Big-M for linking continuous and binary (total_food / 100 is a natural upper bound)
    M = total_food / 100.0

    # Exactly one protein selected
    model.addConstr(y_salmon + y_beef + y_pork == 1, name="one_protein")

    # Protein quantities linked to selection
    model.addConstr(salmon <= M * y_salmon, name="salmon_link")
    model.addConstr(beef <= M * y_beef, name="beef_link")
    model.addConstr(pork <= M * y_pork, name="pork_link")

    # At least min_vegetables vegetables selected
    model.addConstr(z_okra + z_carrots + z_celery + z_cabbage >= min_vegetables, name="min_veg")

    # Vegetable quantities linked to selection
    model.addConstr(okra <= M * z_okra, name="okra_link")
    model.addConstr(carrots <= M * z_carrots, name="carrots_link")
    model.addConstr(celery <= M * z_celery, name="celery_link")
    model.addConstr(cabbage <= M * z_cabbage, name="cabbage_link")

    # Total food intake (in 100g units, total_food is in grams)
    model.addConstr(
        (salmon + beef + pork + okra + carrots + celery + cabbage) == total_food / 100.0,
        name="total_food_constr"
    )

    # Budget constraint (price per 100g * quantity in 100g units)
    model.addConstr(
        price_salmon * salmon + price_beef * beef + price_pork * pork +
        price_okra * okra + price_carrots * carrots +
        price_celery * celery + price_cabbage * cabbage <= budget,
        name="budget_constr"
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