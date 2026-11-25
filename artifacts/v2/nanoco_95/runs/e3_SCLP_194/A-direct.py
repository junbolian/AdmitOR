import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_communities = len(distance_matrix)
    num_depots = len(establishment_cost)

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, num_communities - 1)
    model.depots = pyo.RangeSet(0, num_depots - 1)

    model.open_depot = pyo.Var(model.depots, domain=pyo.Binary)

    def coverage_rule(model_rule, c):
        return sum(
            model_rule.open_depot[d]
            for d in model_rule.depots
            if distance_matrix[c][d] <= coverage_radius
        ) >= 1

    model.coverage = pyo.Constraint(model.communities, rule=coverage_rule)

    def objective_rule(model_rule):
        return sum(
            establishment_cost[d] * model_rule.open_depot[d]
            for d in model_rule.depots
        )

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}