import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_factories = len(activation_cost)
    n_months = len(demand)
    factories = range(n_factories)
    months = range(n_months)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.x = pyo.Var(model.M, model.F, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.M, model.F, domain=pyo.Binary)

    def prod_lower_rule(mdl, mo, fa):
        return mdl.x[mo, fa] >= min_production[fa] * mdl.y[mo, fa]

    def prod_upper_rule(mdl, mo, fa):
        return mdl.x[mo, fa] <= max_production[fa] * mdl.y[mo, fa]

    def demand_rule(mdl, mo):
        return sum(mdl.x[mo, fa] for fa in mdl.F) >= demand[mo]

    model.prod_lower = pyo.Constraint(model.M, model.F, rule=prod_lower_rule)
    model.prod_upper = pyo.Constraint(model.M, model.F, rule=prod_upper_rule)
    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    model.obj = pyo.Objective(
        expr=sum(
            activation_cost[fa] * model.y[mo, fa] + production_cost[fa] * model.x[mo, fa]
            for mo in model.M
            for fa in model.F
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}