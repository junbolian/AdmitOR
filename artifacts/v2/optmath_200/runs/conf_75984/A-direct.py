import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    M = 4  # number of months (structural)
    F = 4  # number of factories (structural)

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.MONTHS = pyo.RangeSet(0, M - 1)
    model.FACTORIES = pyo.RangeSet(0, F - 1)

    model.run = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.Binary)
    model.prod = pyo.Var(model.MONTHS, model.FACTORIES, domain=pyo.NonNegativeReals)

    def prod_lb(mdl, mth, fac):
        return mdl.prod[mth, fac] >= min_production[fac] * mdl.run[mth, fac]

    def prod_ub(mdl, mth, fac):
        return mdl.prod[mth, fac] <= max_production[fac] * mdl.run[mth, fac]

    model.prod_lb_con = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=prod_lb)
    model.prod_ub_con = pyo.Constraint(model.MONTHS, model.FACTORIES, rule=prod_ub)

    def demand_con(mdl, mth):
        return sum(mdl.prod[mth, fac] for fac in mdl.FACTORIES) >= demand[mth]

    model.demand_con = pyo.Constraint(model.MONTHS, rule=demand_con)

    def total_cost(mdl):
        return sum(
            fixed_cost[fac] * mdl.run[mth, fac]
            + variable_cost[fac] * mdl.prod[mth, fac]
            for mth in mdl.MONTHS
            for fac in mdl.FACTORIES
        )

    model.obj = pyo.Objective(rule=total_cost, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}