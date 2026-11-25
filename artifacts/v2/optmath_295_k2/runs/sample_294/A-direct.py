import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.destinations = pyo.RangeSet(0, n_destinations - 1)

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def _obj_rule(m):
        return sum(
            transport_cost[i][j] * m.x[i, j]
            for i in m.origins
            for j in m.destinations
        )

    model.total_cost = pyo.Objective(rule=_obj_rule, sense=pyo.minimize)

    def _supply_rule(m, i):
        return sum(m.x[i, j] for j in m.destinations) == supply[i]

    model.supply_constraint = pyo.Constraint(model.origins, rule=_supply_rule)

    def _demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) == demand[j]

    model.demand_constraint = pyo.Constraint(
        model.destinations, rule=_demand_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}