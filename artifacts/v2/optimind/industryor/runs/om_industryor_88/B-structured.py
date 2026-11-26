# IR: {"sets":[],"params":["shirts_available","pants_available","shirts_per_A","pants_per_A","price_A","shirts_per_B","pants_per_B","price_B","min_A","min_B"],"variables":{"packages_A":"NonNegativeIntegers","packages_B":"NonNegativeIntegers"},"constraints":["shirts_per_A*packages_A + shirts_per_B*packages_B <= shirts_available","pants_per_A*packages_A + pants_per_B*packages_B <= pants_available","packages_A >= min_A","packages_B >= min_B"],"objective":{"sense":"maximize","expression":"price_A*packages_A + price_B*packages_B"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.shirts_available = pyo.Param(initialize=params["shirts_available"])
    model.pants_available = pyo.Param(initialize=params["pants_available"])
    model.shirts_per_A = pyo.Param(initialize=params["shirts_per_A"])
    model.pants_per_A = pyo.Param(initialize=params["pants_per_A"])
    model.price_A = pyo.Param(initialize=params["price_A"])
    model.shirts_per_B = pyo.Param(initialize=params["shirts_per_B"])
    model.pants_per_B = pyo.Param(initialize=params["pants_per_B"])
    model.price_B = pyo.Param(initialize=params["price_B"])
    model.min_A = pyo.Param(initialize=params["min_A"])
    model.min_B = pyo.Param(initialize=params["min_B"])

    model.packages_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.packages_B = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.shirt_inventory_limit = pyo.Constraint(
        expr=(
            model.shirts_per_A * model.packages_A
            + model.shirts_per_B * model.packages_B
            <= model.shirts_available
        )
    )
    model.pants_inventory_limit = pyo.Constraint(
        expr=(
            model.pants_per_A * model.packages_A
            + model.pants_per_B * model.packages_B
            <= model.pants_available
        )
    )
    model.minimum_A_sales = pyo.Constraint(
        expr=model.packages_A >= model.min_A
    )
    model.minimum_B_sales = pyo.Constraint(
        expr=model.packages_B >= model.min_B
    )

    model.total_revenue = pyo.Objective(
        expr=(
            model.price_A * model.packages_A
            + model.price_B * model.packages_B
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "no solution can be loaded" in str(exc).lower():
            return {"objective": None, "status": "no feasible solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}