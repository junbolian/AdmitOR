import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    areas = list(range(25))
    towers = list(range(18))

    coverage = {
        0: [1, 4, 7, 8, 9, 13, 15, 16],
        1: [7, 9, 11, 12, 13, 14, 15, 16],
        2: [1, 2, 4, 5, 7, 9, 10, 11, 14, 17],
        3: [1, 3, 4, 7, 8, 13, 14, 17],
        4: [5, 6, 7, 9, 10, 13, 16, 17],
        5: [0, 1, 3, 4, 9, 10, 12, 14, 17],
        6: [0, 3, 4, 5, 6, 9, 10, 12, 14, 15, 16, 17],
        7: [3, 4, 5, 6, 7, 8, 11, 13, 14],
        8: [0, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15],
        9: [1, 2, 3, 4, 7, 8, 10, 11, 12, 15, 16, 17],
        10: [2, 8, 10, 15, 16],
        11: [0, 2, 3, 5, 12, 13, 14, 15, 17],
        12: [2, 4, 5, 7, 8, 10, 12, 14, 17],
        13: [2, 5, 7, 8, 9, 15, 16],
        14: [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 15],
        15: [0, 1, 3, 4, 6, 7, 8, 9, 10, 13, 15, 16, 17],
        16: [0, 2, 3, 4, 9, 10, 12, 13, 14, 17],
        17: [0, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15],
        18: [2, 4, 5, 7, 9, 10, 11, 12, 16, 17],
        19: [0, 2, 5, 6, 8, 9, 12, 13, 15, 16, 17],
        20: [1, 2, 4, 5, 8, 10, 13, 14, 16],
        21: [0, 1, 3, 4, 7, 10, 12, 14, 17],
        22: [4, 5, 7, 9, 11, 14, 15, 16],
        23: [4, 11, 14, 16],
        24: [9, 11, 17],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.Set(initialize=towers)
    model.AREAS = pyo.Set(initialize=areas)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget
    model.budget_con = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, a):
        return m.covered[a] <= sum(m.build[t] for t in coverage[a])
    model.coverage_con = pyo.Constraint(model.AREAS, rule=coverage_rule)

    def obj_rule(m):
        return sum(population[a] * m.covered[a] for a in m.AREAS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}