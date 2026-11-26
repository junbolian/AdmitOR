import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: packages produced
    model.meaties = pyo.Var(domain=pyo.NonNegativeReals)
    model.yummies = pyo.Var(domain=pyo.NonNegativeReals)

    # Unit margin (revenue - variable blend/pack cost)
    meaties_margin = (
        params["meaties_price"]
        - params["meaties_cereal_per_pkg"] * params["cereal_cost_per_lb"]
        - params["meaties_meat_per_pkg"] * params["meat_cost_per_lb"]
        - params["meaties_blend_pack_cost"]
    )
    yummies_margin = (
        params["yummies_price"]
        - params["yummies_cereal_per_pkg"] * params["cereal_cost_per_lb"]
        - params["yummies_meat_per_pkg"] * params["meat_cost_per_lb"]
        - params["yummies_blend_pack_cost"]
    )

    model.profit = pyo.Objective(
        expr=meaties_margin * model.meaties + yummies_margin * model.yummies,
        sense=pyo.maximize,
    )

    # Cereal capacity
    model.cereal_limit = pyo.Constraint(
        expr=params["meaties_cereal_per_pkg"] * model.meaties
        + params["yummies_cereal_per_pkg"] * model.yummies
        <= params["cereal_capacity"]
    )

    # Meat capacity
    model.meat_limit = pyo.Constraint(
        expr=params["meaties_meat_per_pkg"] * model.meaties
        + params["yummies_meat_per_pkg"] * model.yummies
        <= params["meat_capacity"]
    )

    # Meaties machine capacity
    model.machine_limit = pyo.Constraint(
        expr=model.meaties <= params["meaties_machine_capacity"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}