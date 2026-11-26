import gurobipy as gp
from gurobipy import GRB

def solve(params):
    painting_value = params["painting_value"]
    bust_value = params["bust_value"]
    vase_value = params["vase_value"]
    porsche_value = params["porsche_value"]
    diamond_value = params["diamond_value"]
    diamond_count = params["diamond_count"]
    sofa_value = params["sofa_value"]
    dog_value = params["dog_value"]
    dog_count = params["dog_count"]
    sculpture_value = params["sculpture_value"]
    sailboat_value = params["sailboat_value"]
    harley_value = params["harley_value"]
    cavour_furniture_value = params["cavour_furniture_value"]

    # Items and their values
    # Dogs must stay together, so treat them as a single bundle
    # Diamonds are individual items (diamond_count of them)
    item_values = (
        [painting_value, bust_value, vase_value, porsche_value]
        + [diamond_value] * int(diamond_count)
        + [sofa_value]
        + [dog_value * int(dog_count)]  # dogs as a bundle
        + [sculpture_value, sailboat_value, harley_value, cavour_furniture_value]
    )

    n_items = len(item_values)
    total_value = sum(item_values)

    model = gp.Model("inheritance_division")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if item i goes to son 1, 0 if it goes to son 2
    x = model.addVars(n_items, vtype=GRB.BINARY, name="x")

    # Value assigned to son 1
    son1_value = gp.quicksum(item_values[i] * x[i] for i in range(n_items))

    # d = absolute difference between son1 and son2 shares
    # son2_value = total_value - son1_value
    # difference = |son1_value - son2_value| = |2*son1_value - total_value|
    d = model.addVar(lb=0.0, name="d")

    model.addConstr(d >= son1_value - (total_value - son1_value), name="diff_pos")
    model.addConstr(d >= (total_value - son1_value) - son1_value, name="diff_neg")

    model.setObjective(d, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}