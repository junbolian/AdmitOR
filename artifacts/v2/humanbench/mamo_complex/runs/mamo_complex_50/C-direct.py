import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cereal_capacity = params["cereal_capacity"]
    meat_capacity = params["meat_capacity"]
    cereal_cost_per_lb = params["cereal_cost_per_lb"]
    meat_cost_per_lb = params["meat_cost_per_lb"]
    meaties_price = params["meaties_price"]
    yummies_price = params["yummies_price"]
    meaties_cereal_per_pkg = params["meaties_cereal_per_pkg"]
    meaties_meat_per_pkg = params["meaties_meat_per_pkg"]
    yummies_cereal_per_pkg = params["yummies_cereal_per_pkg"]
    yummies_meat_per_pkg = params["yummies_meat_per_pkg"]
    meaties_blend_pack_cost = params["meaties_blend_pack_cost"]
    yummies_blend_pack_cost = params["yummies_blend_pack_cost"]
    meaties_machine_capacity = params["meaties_machine_capacity"]

    model = gp.Model("healthy_pet_food")
    model.setParam("OutputFlag", 0)

    meaties = model.addVar(lb=0.0, name="meaties")
    yummies = model.addVar(lb=0.0, name="yummies")

    meaties_revenue = meaties_price * meaties
    yummies_revenue = yummies_price * yummies

    meaties_cereal_cost = cereal_cost_per_lb * meaties_cereal_per_pkg * meaties
    meaties_meat_cost = meat_cost_per_lb * meaties_meat_per_pkg * meaties
    yummies_cereal_cost = cereal_cost_per_lb * yummies_cereal_per_pkg * yummies
    yummies_meat_cost = meat_cost_per_lb * yummies_meat_per_pkg * yummies

    meaties_pack_cost = meaties_blend_pack_cost * meaties
    yummies_pack_cost = yummies_blend_pack_cost * yummies

    profit = (
        meaties_revenue + yummies_revenue
        - meaties_cereal_cost - meaties_meat_cost
        - yummies_cereal_cost - yummies_meat_cost
        - meaties_pack_cost - yummies_pack_cost
    )

    model.setObjective(profit, GRB.MAXIMIZE)

    model.addConstr(
        meaties_cereal_per_pkg * meaties + yummies_cereal_per_pkg * yummies <= cereal_capacity,
        name="cereal_limit"
    )
    model.addConstr(
        meaties_meat_per_pkg * meaties + yummies_meat_per_pkg * yummies <= meat_capacity,
        name="meat_limit"
    )
    model.addConstr(
        meaties <= meaties_machine_capacity,
        name="meaties_machine_limit"
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