import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_destinations = len(demand)

    origins = list(range(n_origins))
    destinations = list(range(n_destinations))

    model = pyo.ConcreteModel()

    model.ORIGINS = pyo.Set(initialize=origins)
    model.DESTINATIONS = pyo.Set(initialize=destinations)
    model.LINKS = pyo.Set(
        initialize=[(o, d) for o in origins for d in destinations],
        dimen=2,
    )

    model.x = pyo.Var(model.LINKS, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[o][d] * model.x[o, d] for o in origins for d in destinations),
        sense=pyo.minimize,
    )

    def supply_rule(mdl, o):
        return sum(mdl.x[o, d] for d in destinations) == supply[o]

    model.supply_constraint = pyo.Constraint(model.ORIGINS, rule=supply_rule)

    def demand_rule(mdl, d):
        return sum(mdl.x[o, d] for o in origins) == demand[d]

    model.demand_constraint = pyo.Constraint(model.DESTINATIONS, rule=demand_rule)

    def capacity_rule(mdl, o, d):
        return mdl.x[o, d] <= capacity[o][d]

    model.capacity_constraint = pyo.Constraint(model.LINKS, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}