# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"supply":"params['supply'][o][p]","demand":"params['demand'][d][p]","cost":"params['cost'][o][d][p]","capacity":"params['capacity'][o][d]"},"variables":{"x[o,d,p]":"continuous, nonnegative"},"constraints":["sum(d in D) x[o,d,p] = supply[o,p] for each o,p","sum(o in O) x[o,d,p] = demand[d,p] for each d,p","sum(p in P) x[o,d,p] <= capacity[o,d] for each o,d"],"objective":"minimize sum(o in O,d in D,p in P) cost[o,d,p]*x[o,d,p]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.O = pyo.RangeSet(0, 3)
    model.D = pyo.RangeSet(0, 4)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.O,
        model.P,
        initialize={
            (o, p): params["supply"][o][p]
            for o in model.O
            for p in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.D,
        model.P,
        initialize={
            (d, p): params["demand"][d][p]
            for d in model.D
            for p in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.O,
        model.D,
        model.P,
        initialize={
            (o, d, p): params["cost"][o][d][p]
            for o in model.O
            for d in model.D
            for p in model.P
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.O,
        model.D,
        initialize={
            (o, d): params["capacity"][o][d]
            for o in model.O
            for d in model.D
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.O, model.D, model.P, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, o, p):
        return sum(mdl.x[o, d, p] for d in mdl.D) == mdl.supply[o, p]

    def demand_rule(mdl, d, p):
        return sum(mdl.x[o, d, p] for o in mdl.O) == mdl.demand[d, p]

    def capacity_rule(mdl, o, d):
        return sum(mdl.x[o, d, p] for p in mdl.P) <= mdl.capacity[o, d]

    model.supply_balance = pyo.Constraint(
        model.O, model.P, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.D, model.P, rule=demand_rule
    )
    model.route_capacity = pyo.Constraint(
        model.O, model.D, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[o, d, p] * model.x[o, d, p]
            for o in model.O
            for d in model.D
            for p in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}