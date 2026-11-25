import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_fact = 6
    num_months = 6

    factories = list(range(num_fact))
    months = list(range(num_months))

    min_prod = params["min_production"]
    max_prod = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    def _get(data, i):
        try:
            return data[i]
        except (TypeError, IndexError, KeyError):
            return data

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run_decision = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    model.fixed_term = pyo.Expression(
        expr=sum(
            _get(fixed_cost, f) * model.run_decision[f, m]
            for f in model.F
            for m in model.M
        )
    )
    model.variable_term = pyo.Expression(
        expr=sum(
            _get(variable_cost, f) * model.prod[f, m]
            for f in model.F
            for m in model.M
        )
    )

    model.total_cost = pyo.Objective(
        expr=model.fixed_term + model.variable_term, sense=pyo.minimize
    )

    model.min_prod_con = pyo.Constraint(
        model.F,
        model.M,
        rule=lambda model, f, m: model.prod[f, m] >= _get(min_prod, f) * model.run_decision[f, m],
    )

    model.max_prod_con = pyo.Constraint(
        model.F,
        model.M,
        rule=lambda model, f, m: model.prod[f, m] <= _get(max_prod, f) * model.run_decision[f, m],
    )

    model.demand_con = pyo.Constraint(
        model.M,
        rule=lambda model, m: sum(model.prod[f, m] for f in model.F) >= _get(demand, m),
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}