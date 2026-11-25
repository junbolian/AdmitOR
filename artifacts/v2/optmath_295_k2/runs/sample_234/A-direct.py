import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    coverage = params["coverage"]

    n_areas = len(population)
    n_towers = len(tower_cost)

    model = pyo.ConcreteModel()

    model.AREAS = pyo.Set(initialize=range(n_areas))
    model.TOWERS = pyo.Set(initialize=range(n_towers))

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    def cover_rule(m, a):
        return m.covered[a] <= sum(
            m.build[t] for t in m.TOWERS if coverage[a][t] == 1
        )

    model.cover_con = pyo.Constraint(model.AREAS, rule=cover_rule)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build[t] for t in m.TOWERS) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    model.obj = pyo.Objective(
        expr=sum(population[a] * model.covered[a] for a in model.AREAS),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}