import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    n_fact = len(fixed_cost)
    n_month = len(demand)
    factories = list(range(n_fact))
    months = list(range(n_month))

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.y = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.x = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    model.fixed_cost_c = pyo.Param(model.F, initialize={f: fixed_cost[f] for f in factories}, mutable=False)
    model.var_cost_c = pyo.Param(model.F, initialize={f: variable_cost[f] for f in factories}, mutable=False)
    model.min_prod_c = pyo.Param(model.F, initialize={f: min_production[f] for f in factories}, mutable=False)
    model.max_prod_c = pyo.Param(model.F, initialize={f: max_production[f] for f in factories}, mutable=False)
    model.demand_c = pyo.Param(model.M, initialize={m: demand[m] for m in months}, mutable=False)

    def obj_rule(mdl):
        return sum(mdl.fixed_cost_c[f] * mdl.y[f, m] for f in mdl.F for m in mdl.M) + \
               sum(mdl.var_cost_c[f] * mdl.x[f, m] for f in mdl.F for m in mdl.M)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(mdl, f, m):
        return mdl.x[f, m] >= mdl.min_prod_c[f] * mdl.y[f, m]

    model.min_link = pyo.Constraint(model.F, model.M, rule=min_rule)

    def max_rule(mdl, f, m):
        return mdl.x[f, m] <= mdl.max_prod_c[f] * mdl.y[f, m]

    model.max_link = pyo.Constraint(model.F, model.M, rule=max_rule)

    def demand_rule(mdl, m):
        return sum(mdl.x[f, m] for f in mdl.F) >= mdl.demand_c[m]

    model.demand_sat = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}