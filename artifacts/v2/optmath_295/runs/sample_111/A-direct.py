import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    budget = params["budget"]
    population = params["population"]
    tower_cost = params["tower_cost"]

    n_towers = 8
    n_areas = 11

    # Coverage: which towers can serve each area
    coverage = {
        0: [3],
        1: [0, 1, 2, 3, 7],
        2: [1, 2, 6],
        3: [0, 4, 5, 6],
        4: [3, 5],
        5: [3, 5],
        6: [0, 3, 4],
        7: [2, 3, 4, 5],
        8: [2, 4, 5],
        9: [2, 5],
        10: [1, 2, 3, 4, 5],
    }

    model = pyo.ConcreteModel()
    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.AREAS = pyo.RangeSet(0, n_areas - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.cover = pyo.Var(model.AREAS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(population[a] * m.cover[a] for a in m.AREAS)

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def cover_rule(m, a):
        return m.cover[a] <= sum(m.build[t] for t in coverage[a])

    model.cover_con = pyo.Constraint(model.AREAS, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}