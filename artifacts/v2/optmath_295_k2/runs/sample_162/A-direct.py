import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    factories = range(6)
    months = range(4)

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=list(factories))
    model.M = pyo.Set(initialize=list(months))

    model.run = pyo.Var(model.M, model.F, domain=pyo.Binary)
    model.prod = pyo.Var(model.M, model.F, domain=pyo.NonNegativeReals)

    fixed_cost = {}
    for f in factories:
        for mth in months:
            fixed_cost[(mth, f)] = params[f"fixed_cost_f{f}_month{mth}"]

    var_cost = {f: params[f"var_cost_f{f}"] for f in factories}
    min_prod = {f: params[f"min_prod_f{f}"] for f in factories}
    max_prod = {f: params[f"max_prod_f{f}"] for f in factories}
    demand = {mth: params[f"demand_month{mth}"] for mth in months}

    def obj_rule(mdl):
        return sum(
            fixed_cost[(mth, f)] * mdl.run[mth, f] + var_cost[f] * mdl.prod[mth, f]
            for mth in mdl.M for f in mdl.F
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def min_rule(mdl, mth, f):
        return mdl.prod[mth, f] >= min_prod[f] * mdl.run[mth, f]

    model.min_con = pyo.Constraint(model.M, model.F, rule=min_rule)

    def max_rule(mdl, mth, f):
        return mdl.prod[mth, f] <= max_prod[f] * mdl.run[mth, f]

    model.max_con = pyo.Constraint(model.M, model.F, rule=max_rule)

    def demand_rule(mdl, mth):
        return sum(mdl.prod[mth, f] for f in mdl.F) >= demand[mth]

    model.demand_con = pyo.Constraint(model.M, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}