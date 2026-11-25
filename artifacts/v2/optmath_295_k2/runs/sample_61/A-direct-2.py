import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    n_regions = len(population)
    n_towers = len(tower_cost)

    # coverage[r] = list of tower indices that can cover region r
    coverage = {
        0: [1, 2, 4, 5, 6],
        1: [0, 1, 3, 6],
        2: [0, 1, 2, 4],
        3: [0, 1, 2, 3, 5],
        4: [0, 1, 2, 3, 5],
        5: [0, 1, 2, 6],
        6: [3],
        7: [3, 4, 6],
        8: [0, 2],
        9: [1, 3, 4, 5],
        10: [1, 3, 5, 6],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n_towers - 1)
    model.REGIONS = pyo.RangeSet(0, n_regions - 1)

    # x[j] = 1 if tower j is built
    model.x = pyo.Var(model.TOWERS, domain=pyo.Binary, bounds=(0, 1))
    # y[r] = 1 if region r is covered
    model.y = pyo.Var(model.REGIONS, domain=pyo.Binary, bounds=(0, 1))

    # Budget constraint
    model.budget_con = pyo.Constraint(
        expr=sum(tower_cost[j] * model.x[j] for j in model.TOWERS) <= budget
    )

    # Coverage linking constraints: y[r] <= sum of x[j] for j covering r
    def cover_rule(mdl, r):
        return mdl.y[r] <= sum(mdl.x[j] for j in coverage[r])

    model.cover_con = pyo.Constraint(model.REGIONS, rule=cover_rule)

    # Objective: maximize total population covered
    model.obj = pyo.Objective(
        expr=sum(population[r] * model.y[r] for r in model.REGIONS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}