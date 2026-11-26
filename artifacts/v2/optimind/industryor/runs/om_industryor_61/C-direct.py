import gurobipy as gp
from gurobipy import GRB


def solve(params):
    demand = params["demand"]
    poll_h = params["pollution_horse"]
    poll_b = params["pollution_bicycle"]
    poll_hc = params["pollution_handcart"]
    poll_budget = params["pollution_budget"]
    min_horse = params["min_horse_trips"]
    cap_h = params["capacity_horse"]
    cap_b = params["capacity_bicycle"]
    cap_hc = params["capacity_handcart"]

    model = gp.Model("farm_transport")
    model.Params.OutputFlag = 0

    horse = model.addVar(vtype=GRB.INTEGER, lb=min_horse, name="horse")
    bicycle = model.addVar(vtype=GRB.INTEGER, lb=0, name="bicycle")
    handcart = model.addVar(vtype=GRB.INTEGER, lb=0, name="handcart")

    use_bicycle = model.addVar(vtype=GRB.BINARY, name="use_bicycle")
    use_handcart = model.addVar(vtype=GRB.BINARY, name="use_handcart")

    # Choose at most one of bicycle / handcart
    model.addConstr(use_bicycle + use_handcart <= 1, name="one_method")

    # Big-M linking trips to selection
    big_m = 10 ** 6
    model.addConstr(bicycle <= big_m * use_bicycle, name="link_bicycle")
    model.addConstr(handcart <= big_m * use_handcart, name="link_handcart")

    # Total produce transported
    model.addConstr(
        cap_h * horse + cap_b * bicycle + cap_hc * handcart >= demand,
        name="demand",
    )

    # Pollution budget
    model.addConstr(
        poll_h * horse + poll_b * bicycle + poll_hc * handcart <= poll_budget,
        name="pollution_budget",
    )

    model.setObjective(
        poll_h * horse + poll_b * bicycle + poll_hc * handcart, GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed: status " + str(model.Status)}