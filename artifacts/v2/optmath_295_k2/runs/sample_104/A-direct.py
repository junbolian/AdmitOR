import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_regions = len(population)
    n_towers = len(tower_cost)

    coverage = {
        0: [0, 3, 5, 7],
        1: [2, 6],
        2: [1, 3, 5],
        3: [0, 2, 5, 6, 7],
        4: [4, 6],
        5: [0, 1, 2, 5, 6],
        6: [1, 3, 4, 6],
        7: [0, 1, 6],
        8: [4, 5, 6, 7],
        9: [3, 4, 5, 6],
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, n_regions - 1)
    model.towers = pyo.RangeSet(0, n_towers - 1)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    def objective_rule(m):
        return sum(population[i] * m.covered[i] for i in m.regions)

    model.total_population = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[j] * m.build[j] for j in m.towers) <= budget

    model.budget_constraint = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, i):
        return m.covered[i] <= sum(m.build[j] for j in coverage[i])

    model.coverage_constraint = pyo.Constraint(model.regions, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_population))
    return {"objective": obj_val, "status": "optimal"}