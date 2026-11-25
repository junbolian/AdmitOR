import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    population = params["population"]

    towers = list(range(9))
    regions = list(range(11))

    coverage_map = {
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

    model.TOWERS = pyo.Set(initialize=towers)
    model.REGIONS = pyo.Set(initialize=regions)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.cover = pyo.Var(model.REGIONS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(population[r] * m.cover[r] for r in m.REGIONS)

    model.total_population = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget

    model.budget_constraint = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, r):
        return m.cover[r] <= sum(m.build[t] for t in coverage_map[r])

    model.coverage_constraint = pyo.Constraint(model.REGIONS, rule=coverage_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_population))
    return {"objective": obj_val, "status": "optimal"}