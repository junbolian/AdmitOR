import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    factories = range(4)
    months = range(5)

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    m = pyo.ConcreteModel()

    m.F = pyo.Set(initialize=list(factories))
    m.M = pyo.Set(initialize=list(months))

    m.run = pyo.Var(m.F, m.M, domain=pyo.Binary)
    m.prod = pyo.Var(m.F, m.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(fixed_cost[i] * mdl.run[i, t] for i in mdl.F for t in mdl.M) + \
               sum(variable_cost[i] * mdl.prod[i, t] for i in mdl.F for t in mdl.M)
    m.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_prod_rule(mdl, i, t):
        return mdl.prod[i, t] >= min_production[i] * mdl.run[i, t]
    m.min_prod_con = pyo.Constraint(m.F, m.M, rule=min_prod_rule)

    def max_prod_rule(mdl, i, t):
        return mdl.prod[i, t] <= max_production[i] * mdl.run[i, t]
    m.max_prod_con = pyo.Constraint(m.F, m.M, rule=max_prod_rule)

    def demand_rule(mdl, t):
        return sum(mdl.prod[i, t] for i in mdl.F) >= demand[t]
    m.demand_con = pyo.Constraint(m.M, rule=demand_rule)

    Highs().solve(m)
    obj_val = float(pyo.value(m.obj))
    return {"objective": obj_val, "status": "optimal"}

model = None