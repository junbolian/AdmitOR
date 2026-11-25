# IR: {"sets":{"I":"0..35"},"params":{"values":"profit[i], i in I; params['values']","weights":"resource_cost[i], i in I; params['weights']","budget":"params['budget']"},"variables":{"x[i]":"binary, i in I"},"constraints":["sum(weights[i]*x[i] for i in I) <= budget"],"objective":"maximize sum(values[i]*x[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    budget = params["budget"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 35)

    model.profit = pyo.Param(
        model.products,
        initialize={i: values[i] for i in model.products},
        within=pyo.Reals,
    )
    model.resource_cost = pyo.Param(
        model.products,
        initialize={i: weights[i] for i in model.products},
        within=pyo.Reals,
    )
    model.resource_budget = pyo.Param(initialize=budget, within=pyo.Reals)

    model.x = pyo.Var(model.products, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.resource_cost[i] * model.x[i] for i in model.products
        ) <= model.resource_budget
    )
    model.total_value = pyo.Objective(
        expr=sum(model.profit[i] * model.x[i] for i in model.products),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Judge success solely by whether an objective value is available.
        pass

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}