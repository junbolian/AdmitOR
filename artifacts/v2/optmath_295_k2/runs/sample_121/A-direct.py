import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n_origins = len(supply)
    n_destinations = len(demand)

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, n_origins - 1)
    model.destinations = pyo.RangeSet(0, n_destinations - 1)

    model.x = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.destinations) == supply[i]

    model.supply_constraint = pyo.Constraint(
        model.origins, rule=supply_rule
    )

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.origins) == demand[j]

    model.demand_constraint = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    def objective_rule(mdl):
        return sum(
            cost_matrix[i][j] * mdl.x[i, j]
            for i in mdl.origins
            for j in mdl.destinations
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}