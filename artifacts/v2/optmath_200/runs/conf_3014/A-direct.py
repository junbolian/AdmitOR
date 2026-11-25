import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_regions = 12
    num_towers = 9

    coverable_by = {
        0: [4, 6, 8],
        1: [2, 5, 7],
        2: [0, 3, 4, 5, 6, 7, 8],
        3: [0, 2, 3, 7],
        4: [0, 1, 4, 5, 7],
        5: [1, 2],
        6: [0, 1, 3, 4, 5, 6, 8],
        7: [3, 4, 6, 8],
        8: [1, 2, 3, 6, 8],
        9: [1, 5, 8],
        10: [3, 5, 6],
        11: [0, 2, 3, 4, 5, 8],
    }

    model = pyo.ConcreteModel()

    model.T = pyo.RangeSet(0, num_towers - 1)
    model.R = pyo.RangeSet(0, num_regions - 1)

    model.build = pyo.Var(model.T, domain=pyo.Binary)
    model.covered = pyo.Var(model.R, domain=pyo.Binary)

    def obj_rule(m):
        return sum(population[r] * m.covered[r] for r in m.R)

    model.total_coverage = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.T) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, r):
        return m.covered[r] <= sum(m.build[t] for t in coverable_by[r])

    model.coverage_con = pyo.Constraint(model.R, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_coverage))
    return {"objective": obj_val, "status": "optimal"}