import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_towers = 8
    n_areas = 11

    coverage = [
        [3],
        [0, 1, 2, 3, 7],
        [1, 2, 6],
        [0, 4, 5, 6],
        [3, 5],
        [3, 5],
        [0, 3, 4],
        [2, 3, 4, 5],
        [2, 4, 5],
        [2, 5],
        [1, 2, 3, 4, 5],
    ]

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.AREAS = pyo.RangeSet(0, n_areas - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget
    model.budget_con = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, a):
        return m.covered[a] <= sum(m.build[t] for t in coverage[a])
    model.coverage_con = pyo.Constraint(model.AREAS, rule=coverage_rule)

    def objective_rule(m):
        return sum(population[a] * m.covered[a] for a in m.AREAS)
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}