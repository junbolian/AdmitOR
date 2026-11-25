import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    num_towers = len(tower_cost)
    num_areas = len(population)

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

    model.TOWERS = pyo.RangeSet(0, num_towers - 1)
    model.AREAS = pyo.RangeSet(0, num_areas - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[j] * model.build[j] for j in model.TOWERS) <= budget
    )

    def cover_rule(mdl, i):
        return mdl.covered[i] <= sum(mdl.build[j] for j in coverage[i])

    model.cover_con = pyo.Constraint(model.AREAS, rule=cover_rule)

    model.obj = pyo.Objective(
        expr=sum(population[i] * model.covered[i] for i in model.AREAS),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}