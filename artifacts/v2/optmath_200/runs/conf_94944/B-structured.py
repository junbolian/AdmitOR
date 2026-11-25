# IR: {"sets":{"W":[0,1,2,3,4],"S":[0,1,2,3,4,5],"P":[0,1]},"params":{"supply":"params['supply'][w][p]","demand":"params['demand'][s][p]","cost":"params['cost'][p][w][s]","link_capacity":"params['link_capacity'][w][s]"},"variables":{"ship[w,s,p]":"NonNegativeReals"},"constraints":["sum(s in S, ship[w,s,p]) <= supply[w,p] for w in W, p in P","sum(w in W, ship[w,s,p]) == demand[s,p] for s in S, p in P","sum(p in P, ship[w,s,p]) <= link_capacity[w,s] for w in W, s in S"],"objective":"minimize sum(w in W, s in S, p in P, cost[p,w,s] * ship[w,s,p])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 4)
    model.S = pyo.RangeSet(0, 5)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.W,
        model.P,
        initialize={
            (warehouse, product): params["supply"][warehouse][product]
            for warehouse in model.W
            for product in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.S,
        model.P,
        initialize={
            (store, product): params["demand"][store][product]
            for store in model.S
            for product in model.P
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.W,
        model.S,
        initialize={
            (product, warehouse, store): params["cost"][product][warehouse][store]
            for product in model.P
            for warehouse in model.W
            for store in model.S
        },
        within=pyo.Reals,
    )
    model.link_capacity = pyo.Param(
        model.W,
        model.S,
        initialize={
            (warehouse, store): params["link_capacity"][warehouse][store]
            for warehouse in model.W
            for store in model.S
        },
        within=pyo.NonNegativeReals,
    )

    model.ship = pyo.Var(
        model.W, model.S, model.P, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, warehouse, product):
        return (
            sum(mdl.ship[warehouse, store, product] for store in mdl.S)
            <= mdl.supply[warehouse, product]
        )

    model.supply_limits = pyo.Constraint(
        model.W, model.P, rule=supply_rule
    )

    def demand_rule(mdl, store, product):
        return (
            sum(mdl.ship[warehouse, store, product] for warehouse in mdl.W)
            == mdl.demand[store, product]
        )

    model.demand_requirements = pyo.Constraint(
        model.S, model.P, rule=demand_rule
    )

    def capacity_rule(mdl, warehouse, store):
        return (
            sum(mdl.ship[warehouse, store, product] for product in mdl.P)
            <= mdl.link_capacity[warehouse, store]
        )

    model.transport_limits = pyo.Constraint(
        model.W, model.S, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[product, warehouse, store]
            * model.ship[warehouse, store, product]
            for warehouse in model.W
            for store in model.S
            for product in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}