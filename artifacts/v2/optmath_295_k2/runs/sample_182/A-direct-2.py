import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    factories = list(range(6))
    months = list(range(4))

    min_prod = params["min_production"]
    max_prod = params["max_production"]
    demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    # Normalize scalar-or-list params into per-factory lists
    def as_list(val):
        if isinstance(val, (list, tuple)):
            return list(val)
        return [val] * len(factories)

    min_prod_f = as_list(min_prod)
    max_prod_f = as_list(max_prod)
    demand_m = list(demand) if isinstance(demand, (list, tuple)) else [demand] * len(months)
    fixed_f = as_list(fixed_cost)
    var_f = as_list(variable_cost)

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=factories)
    model.M = pyo.Set(initialize=months)

    model.run = pyo.Var(model.F, model.M, domain=pyo.Binary)
    model.prod = pyo.Var(model.F, model.M, domain=pyo.NonNegativeReals)

    # Min/max production linking with run decision
    def min_rule(m, f, t):
        return m.prod[f, t] >= min_prod_f[f] * m.run[f, t]

    def max_rule(m, f, t):
        return m.prod[f, t] <= max_prod_f[f] * m.run[f, t]

    model.min_link = pyo.Constraint(model.F, model.M, rule=min_rule)
    model.max_link = pyo.Constraint(model.F, model.M, rule=max_rule)

    # Demand satisfaction per month
    def demand_rule(m, t):
        return sum(m.prod[f, t] for f in m.F) >= demand_m[t]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    # Objective
    def obj_rule(m):
        return sum(
            fixed_f[f] * m.run[f, t] + var_f[f] * m.prod[f, t]
            for f in m.F for t in m.M
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible"}