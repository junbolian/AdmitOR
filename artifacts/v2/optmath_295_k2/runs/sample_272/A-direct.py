import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_areas = 9
    n_towers = 9

    coverage = {
        0: [2, 4, 5, 6, 7],
        1: [0, 1, 6, 8],
        2: [1, 6, 8],
        3: [1, 2, 6, 7],
        4: [0, 2, 3, 6, 7, 8],
        5: [0, 1, 2, 6, 7],
        6: [0, 1, 2, 4],
        7: [1, 2, 4, 5, 6],
        8: [0, 1, 3, 4, 5, 8],
    }

    # Towers that can serve each area (reverse view is not needed but kept clear)
    servers = {i: coverage[i] for i in range(n_areas)}

    model = pyo.ConcreteModel()

    model.areas = pyo.RangeSet(0, n_areas - 1)
    model.towers = pyo.RangeSet(0, n_towers - 1)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.cover = pyo.Var(model.areas, domain=pyo.Binary)

    # Budget constraint
    model.budget_rule = pyo.Constraint(
        expr=sum(tower_cost[j] * model.build[j] for j in model.towers) <= budget
    )

    # Coverage linking: cover[i] <= sum of build[j] for j that serve i
    def coverage_rule(m, i):
        return m.cover[i] <= sum(m.build[j] for j in servers[i])

    model.coverage_link = pyo.Constraint(model.areas, rule=coverage_rule)

    # Objective
    model.total_pop = pyo.Objective(
        expr=sum(population[i] * model.cover[i] for i in model.areas),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_pop))
    return {"objective": obj_val, "status": "optimal"}