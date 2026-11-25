import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_regions = len(population)
    n_towers = len(tower_cost)

    coverage = {
        0: [0, 3, 5, 6],
        1: [2, 3, 4, 6],
        2: [0, 1, 4, 5, 6],
        3: [0, 3, 4],
        4: [0, 3, 4],
        5: [1, 2, 3],
        6: [1, 2, 3, 4],
        7: [1, 2, 3, 4, 5, 6],
        8: [0, 1, 2, 4, 5],
        9: [1, 4, 6],
    }

    model = pyo.ConcreteModel()

    model.REGIONS = pyo.RangeSet(0, n_regions - 1)
    model.TOWERS = pyo.RangeSet(0, n_towers - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.REGIONS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(population[i] * m.covered[i] for i in m.REGIONS)

    model.total_population = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[j] * m.build[j] for j in m.TOWERS) <= budget

    model.budget_limit = pyo.Constraint(rule=budget_rule)

    def cover_rule(m, i):
        return m.covered[i] <= sum(m.build[j] for j in coverage[i])

    model.coverage_link = pyo.Constraint(model.REGIONS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_population))
    return {"objective": obj_val, "status": "optimal"}