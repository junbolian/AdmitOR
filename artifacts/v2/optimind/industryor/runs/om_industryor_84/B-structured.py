# IR: {"sets":{},"params":["price_meaties","price_yummies","grains_per_meaties","meat_per_meaties","grains_per_yummies","meat_per_yummies","varcost_meaties","varcost_yummies","grains_price","meat_price","grains_avail","meat_avail","meaties_capacity"],"variables":{"meaties":"NonNegativeReals","yummies":"NonNegativeReals"},"constraints":{"grains_limit":"grains_per_meaties*meaties + grains_per_yummies*yummies <= grains_avail","meat_limit":"meat_per_meaties*meaties + meat_per_yummies*yummies <= meat_avail","machine_limit":"meaties <= meaties_capacity"},"objective":{"sense":"maximize","expression":"(price_meaties-varcost_meaties-grains_price*grains_per_meaties-meat_price*meat_per_meaties)*meaties + (price_yummies-varcost_yummies-grains_price*grains_per_yummies-meat_price*meat_per_yummies)*yummies"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    parameter_names = (
        "price_meaties",
        "price_yummies",
        "grains_per_meaties",
        "meat_per_meaties",
        "grains_per_yummies",
        "meat_per_yummies",
        "varcost_meaties",
        "varcost_yummies",
        "grains_price",
        "meat_price",
        "grains_avail",
        "meat_avail",
        "meaties_capacity",
    )
    for parameter_name in parameter_names:
        model.add_component(
            parameter_name,
            pyo.Param(initialize=params[parameter_name], within=pyo.Reals),
        )

    model.meaties = pyo.Var(domain=pyo.NonNegativeReals)
    model.yummies = pyo.Var(domain=pyo.NonNegativeReals)

    model.grains_limit = pyo.Constraint(
        expr=(
            model.grains_per_meaties * model.meaties
            + model.grains_per_yummies * model.yummies
            <= model.grains_avail
        )
    )
    model.meat_limit = pyo.Constraint(
        expr=(
            model.meat_per_meaties * model.meaties
            + model.meat_per_yummies * model.yummies
            <= model.meat_avail
        )
    )
    model.machine_limit = pyo.Constraint(
        expr=model.meaties <= model.meaties_capacity
    )

    model.profit = pyo.Objective(
        expr=(
            (
                model.price_meaties
                - model.varcost_meaties
                - model.grains_price * model.grains_per_meaties
                - model.meat_price * model.meat_per_meaties
            )
            * model.meaties
            + (
                model.price_yummies
                - model.varcost_yummies
                - model.grains_price * model.grains_per_yummies
                - model.meat_price * model.meat_per_yummies
            )
            * model.yummies
        ),
        sense=pyo.maximize,
    )

    # HiGHS can raise RuntimeError when no solution can be loaded.
    # Success is determined exclusively by objective retrievability.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}