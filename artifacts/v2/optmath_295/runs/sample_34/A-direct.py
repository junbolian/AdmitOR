import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_areas = len(population)
    n_towers = len(tower_cost)

    coverage = [
        [0, 1, 4, 5, 6, 7, 11, 12, 14, 16, 18],
        [0, 1, 4, 6, 7, 13, 14, 17],
        [6, 7, 8, 11, 12, 14, 15, 16, 18],
        [1, 2, 4, 5, 8, 9, 12, 13, 14, 17, 18, 19],
        [0, 3, 9, 10, 11, 13, 14, 17, 18, 19],
        [0, 1, 5, 8, 9, 11, 12, 13, 16, 17, 19],
        [0, 2, 3, 4, 6, 7, 9, 14, 17, 19],
        [0, 4, 5, 6, 10, 11, 14, 15, 18],
        [0, 1, 7, 8, 9, 10, 11, 12, 16, 17, 18, 19],
        [5, 10, 15],
        [0, 5, 7, 8, 9, 11, 13, 15, 16, 17, 19],
        [0, 1, 3, 6, 7, 8, 10, 12, 16, 17, 19],
        [1, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        [0, 2, 4, 5, 6, 7, 9, 13, 14, 15, 16, 19],
        [4, 5, 6, 8, 11, 14, 15],
        [0, 1, 2, 8, 10, 11, 17, 19],
        [0, 2, 3, 4, 8, 10, 11, 13, 14, 15, 16, 18],
        [0, 2, 3, 4, 5, 6, 7, 8, 11, 14, 17, 18, 19],
        [2, 5, 8, 11, 13, 15, 16, 18],
        [3, 5, 6, 7, 8, 10, 11, 12, 15, 16, 18, 19],
        [0, 4, 8, 9, 11, 14, 16, 18, 19],
        [0, 4, 5, 6, 7, 9, 10, 15, 17, 18, 19],
    ]

    model = pyo.ConcreteModel()

    model.areas = pyo.RangeSet(0, n_areas - 1)
    model.towers = pyo.RangeSet(0, n_towers - 1)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.cover = pyo.Var(model.areas, domain=pyo.Binary)

    def obj_rule(m):
        return sum(population[a] * m.cover[a] for a in m.areas)

    model.total_population = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.towers) <= budget

    model.budget_constraint = pyo.Constraint(rule=budget_rule)

    def cover_rule(m, a):
        return m.cover[a] <= sum(m.build[t] for t in coverage[a])

    model.cover_constraint = pyo.Constraint(model.areas, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_population))
    return {"objective": obj_val, "status": "optimal"}