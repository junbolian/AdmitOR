import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_towers = 9
    n_regions = 11

    coverage = {
        0: [4, 5, 6, 8],
        1: [1, 2, 3, 4, 5, 7],
        2: [3, 5, 7],
        3: [1, 3, 4, 5, 6],
        4: [0, 3, 4, 7],
        5: [5, 7, 8],
        6: [1, 3, 6, 8],
        7: [6, 7],
        8: [3],
        9: [0, 2, 3, 4, 5, 8],
        10: [1, 2, 4, 6, 7, 8],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.REGIONS = pyo.RangeSet(0, n_regions - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.cover = pyo.Var(model.REGIONS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(population[r] * m.cover[r] for r in m.REGIONS)

    model.total_coverage = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def cover_rule(m, r):
        return m.cover[r] <= sum(m.build[t] for t in coverage[r])

    model.cover_con = pyo.Constraint(model.REGIONS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_coverage))
    return {"objective": obj_val, "status": "optimal"}