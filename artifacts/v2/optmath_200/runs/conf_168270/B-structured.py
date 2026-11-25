# IR: {"sets":{"patterns":[0,1,2,3,4,5,6,7,8,9],"clients":[1,2,3,4]},"params":{"pattern_yields":"10x4 array, indexed [pattern][client-1]","demands":"length-4 array, indexed [client-1]","pattern_upper_bounds":"length-10 array, indexed [pattern]"},"variables":{"usage[p]":"nonnegative integer"},"constraints":["For every client c: sum(pattern_yields[p][c-1]*usage[p] for p in patterns) >= demands[c-1].","For every pattern p: usage[p] <= pattern_upper_bounds[p]."],"objective":"Minimize sum(usage[p] for p in patterns)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pattern_yields = params["pattern_yields"]
    demands = params["demands"]
    pattern_upper_bounds = params["pattern_upper_bounds"]

    model = pyo.ConcreteModel()
    model.patterns = pyo.RangeSet(0, 9)
    model.clients = pyo.RangeSet(1, 4)

    model.sheet_yield = pyo.Param(
        model.patterns,
        model.clients,
        initialize=lambda _, p, c: pattern_yields[p][c - 1],
    )
    model.required_sheets = pyo.Param(
        model.clients,
        initialize=lambda _, c: demands[c - 1],
    )
    model.usage_limit = pyo.Param(
        model.patterns,
        initialize=lambda _, p: pattern_upper_bounds[p],
    )

    model.usage = pyo.Var(model.patterns, domain=pyo.NonNegativeIntegers)

    def demand_rule(instance, c):
        return (
            sum(
                instance.sheet_yield[p, c] * instance.usage[p]
                for p in instance.patterns
            )
            >= instance.required_sheets[c]
        )

    model.demand_constraints = pyo.Constraint(
        model.clients, rule=demand_rule
    )
    model.limit_constraints = pyo.Constraint(
        model.patterns,
        rule=lambda instance, p: instance.usage[p] <= instance.usage_limit[p],
    )
    model.total_rolls = pyo.Objective(
        expr=sum(model.usage[p] for p in model.patterns),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_rolls))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}