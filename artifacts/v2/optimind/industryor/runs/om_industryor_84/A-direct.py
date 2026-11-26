import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Decision variables: packs produced, raw materials purchased
    model.meaties = pyo.Var(domain=pyo.NonNegativeReals)
    model.yummies = pyo.Var(domain=pyo.NonNegativeReals)
    model.grains = pyo.Var(domain=pyo.NonNegativeReals)
    model.meat = pyo.Var(domain=pyo.NonNegativeReals)

    # Profit = revenue - variable costs - raw material costs
    model.profit = pyo.Objective(
        expr=(
            params["price_meaties"] * model.meaties
            + params["price_yummies"] * model.yummies
            - params["varcost_meaties"] * model.meaties
            - params["varcost_yummies"] * model.yummies
            - params["grains_price"] * model.grains
            - params["meat_price"] * model.meat
        ),
        sense=pyo.maximize,
    )

    # Material balance: grains used equals grains purchased
    model.grains_balance = pyo.Constraint(
        expr=model.grains
        == params["grains_per_meaties"] * model.meaties
        + params["grains_per_yummies"] * model.yummies
    )

    # Material balance: meat used equals meat purchased
    model.meat_balance = pyo.Constraint(
        expr=model.meat
        == params["meat_per_meaties"] * model.meaties
        + params["meat_per_yummies"] * model.yummies
    )

    # Purchase availability limits
    model.grains_limit = pyo.Constraint(
        expr=model.grains <= params["grains_avail"]
    )
    model.meat_limit = pyo.Constraint(
        expr=model.meat <= params["meat_avail"]
    )

    # Machine capacity for Meaties
    model.meaties_capacity = pyo.Constraint(
        expr=model.meaties <= params["meaties_capacity"]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}