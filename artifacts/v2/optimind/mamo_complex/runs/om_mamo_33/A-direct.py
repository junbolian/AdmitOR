import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    price_meaties = params["price_meaties"]
    price_yummies = params["price_yummies"]
    cereal_per_meaties = params["cereal_per_meaties"]
    meat_per_meaties = params["meat_per_meaties"]
    cereal_per_yummies = params["cereal_per_yummies"]
    meat_per_yummies = params["meat_per_yummies"]
    varcost_meaties = params["varcost_meaties"]
    varcost_yummies = params["varcost_yummies"]
    cereal_price = params["cereal_price"]
    meat_price = params["meat_price"]
    cereal_avail = params["cereal_avail"]
    meat_avail = params["meat_avail"]
    meaties_capacity = params["meaties_capacity"]

    # Contribution margin per package (revenue - variable packing cost - ingredient cost)
    meaties_margin = (
        price_meaties
        - varcost_meaties
        - cereal_per_meaties * cereal_price
        - meat_per_meaties * meat_price
    )
    yummies_margin = (
        price_yummies
        - varcost_yummies
        - cereal_per_yummies * cereal_price
        - meat_per_yummies * meat_price
    )

    model = pyo.ConcreteModel()

    model.meaties = pyo.Var(domain=pyo.NonNegativeReals)
    model.yummies = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=meaties_margin * model.meaties + yummies_margin * model.yummies,
        sense=pyo.maximize,
    )

    model.cereal_limit = pyo.Constraint(
        expr=cereal_per_meaties * model.meaties
        + cereal_per_yummies * model.yummies
        <= cereal_avail
    )
    model.meat_limit = pyo.Constraint(
        expr=meat_per_meaties * model.meaties
        + meat_per_yummies * model.yummies
        <= meat_avail
    )
    model.meaties_cap = pyo.Constraint(expr=model.meaties <= meaties_capacity)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}