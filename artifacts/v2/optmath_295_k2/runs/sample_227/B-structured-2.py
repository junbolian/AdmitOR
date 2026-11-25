# IR: {"sets":{"products":[1,2,3],"schools":[1,2,3,4]},"params":{"profit_p{p}_s{s}":"real, for every product p and school s","demand_p{p}_s{s}":"real, for every product p and school s"},"variables":{"supplied[p,s]":"nonnegative continuous real"},"constraints":["supplied[p,s] == demand_p{p}_s{s} for every product p and school s"],"objective":"maximize sum(profit_p{p}_s{s} * supplied[p,s] for every product p and school s)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(1, 3)
    model.schools = pyo.RangeSet(1, 4)

    model.unit_profit = pyo.Param(
        model.products,
        model.schools,
        initialize={
            (product, school): params[f"profit_p{product}_s{school}"]
            for product in model.products
            for school in model.schools
        },
        within=pyo.Reals,
    )

    model.required_demand = pyo.Param(
        model.products,
        model.schools,
        initialize={
            (product, school): params[f"demand_p{product}_s{school}"]
            for product in model.products
            for school in model.schools
        },
        within=pyo.Reals,
    )

    model.supplied = pyo.Var(
        model.products,
        model.schools,
        domain=pyo.NonNegativeReals,
    )

    def exact_demand_rule(instance, product, school):
        return (
            instance.supplied[product, school]
            == instance.required_demand[product, school]
        )

    model.exact_demand = pyo.Constraint(
        model.products,
        model.schools,
        rule=exact_demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product, school]
            * model.supplied[product, school]
            for product in model.products
            for school in model.schools
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}