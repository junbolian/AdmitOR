# IR: {"sets":{"products":[1,2,3],"schools":[1,2,3,4]},"params":{"profit[p,s]":"params['profit_p{p}_s{s}'], real","demand[p,s]":"params['demand_p{p}_s{s}'], real"},"variables":{"supply[p,s]":"nonnegative continuous real"},"constraints":["supply[p,s] == demand[p,s] for every product p and school s"],"objective":"maximize sum(profit[p,s] * supply[p,s] for every product p and school s)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(1, 3)
    model.schools = pyo.RangeSet(1, 4)

    model.profit = pyo.Param(
        model.products,
        model.schools,
        initialize={
            (product, school): params[f"profit_p{product}_s{school}"]
            for product in model.products
            for school in model.schools
        },
        within=pyo.Reals,
    )

    model.demand = pyo.Param(
        model.products,
        model.schools,
        initialize={
            (product, school): params[f"demand_p{product}_s{school}"]
            for product in model.products
            for school in model.schools
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.products,
        model.schools,
        domain=pyo.NonNegativeReals,
    )

    def exact_demand_rule(instance, product, school):
        return (
            instance.supply[product, school]
            == instance.demand[product, school]
        )

    model.exact_demand = pyo.Constraint(
        model.products,
        model.schools,
        rule=exact_demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product, school] * model.supply[product, school]
            for product in model.products
            for school in model.schools
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}