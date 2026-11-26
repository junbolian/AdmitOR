# IR: {"sets":[],"params":["price_meaties","price_yummies","cereal_per_meaties","meat_per_meaties","cereal_per_yummies","meat_per_yummies","varcost_meaties","varcost_yummies","cereal_price","meat_price","cereal_avail","meat_avail","meaties_capacity"],"variables":{"x_meaties":"NonNegativeReals","x_yummies":"NonNegativeReals"},"constraints":["cereal_per_meaties*x_meaties+cereal_per_yummies*x_yummies<=cereal_avail","meat_per_meaties*x_meaties+meat_per_yummies*x_yummies<=meat_avail","x_meaties<=meaties_capacity"],"objective":{"sense":"maximize","expression":"(price_meaties-varcost_meaties-cereal_price*cereal_per_meaties-meat_price*meat_per_meaties)*x_meaties+(price_yummies-varcost_yummies-cereal_price*cereal_per_yummies-meat_price*meat_per_yummies)*x_yummies"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    parameter_names = (
        "price_meaties",
        "price_yummies",
        "cereal_per_meaties",
        "meat_per_meaties",
        "cereal_per_yummies",
        "meat_per_yummies",
        "varcost_meaties",
        "varcost_yummies",
        "cereal_price",
        "meat_price",
        "cereal_avail",
        "meat_avail",
        "meaties_capacity",
    )

    model = pyo.ConcreteModel()
    model.input_data = pyo.Param(
        parameter_names,
        initialize={
            parameter_name: params[parameter_name]
            for parameter_name in parameter_names
        },
        within=pyo.Reals,
    )

    model.x_meaties = pyo.Var(domain=pyo.NonNegativeReals)
    model.x_yummies = pyo.Var(domain=pyo.NonNegativeReals)

    model.cereal_limit = pyo.Constraint(
        expr=(
            model.input_data["cereal_per_meaties"] * model.x_meaties
            + model.input_data["cereal_per_yummies"] * model.x_yummies
            <= model.input_data["cereal_avail"]
        )
    )

    model.meat_limit = pyo.Constraint(
        expr=(
            model.input_data["meat_per_meaties"] * model.x_meaties
            + model.input_data["meat_per_yummies"] * model.x_yummies
            <= model.input_data["meat_avail"]
        )
    )

    model.meaties_machine_limit = pyo.Constraint(
        expr=model.x_meaties <= model.input_data["meaties_capacity"]
    )

    model.total_profit = pyo.Objective(
        expr=(
            (
                model.input_data["price_meaties"]
                - model.input_data["varcost_meaties"]
                - model.input_data["cereal_price"]
                * model.input_data["cereal_per_meaties"]
                - model.input_data["meat_price"]
                * model.input_data["meat_per_meaties"]
            )
            * model.x_meaties
            + (
                model.input_data["price_yummies"]
                - model.input_data["varcost_yummies"]
                - model.input_data["cereal_price"]
                * model.input_data["cereal_per_yummies"]
                - model.input_data["meat_price"]
                * model.input_data["meat_per_yummies"]
            )
            * model.x_yummies
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}