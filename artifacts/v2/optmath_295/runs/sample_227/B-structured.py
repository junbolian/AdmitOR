# IR: {"sets":{"P":[1,2,3],"S":[1,2,3,4]},"params":{"profit[p,s]":"params['profit_p{p}_s{s}'], real, p in P, s in S","demand[p,s]":"params['demand_p{p}_s{s}'], real, p in P, s in S"},"variables":{"x[p,s]":"nonnegative real, p in P, s in S"},"constraints":["x[p,s] == demand[p,s] for each p in P, s in S"],"objective":"maximize sum(profit[p,s] * x[p,s] for p in P, s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.schools = pyo.Set(initialize=[1, 2, 3, 4], ordered=True)

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

    model.x = pyo.Var(
        model.products,
        model.schools,
        domain=pyo.NonNegativeReals,
    )

    def exact_demand_rule(instance, product, school):
        return instance.x[product, school] == instance.demand[product, school]

    model.exact_demand = pyo.Constraint(
        model.products,
        model.schools,
        rule=exact_demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product, school] * model.x[product, school]
            for product in model.products
            for school in model.schools
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}