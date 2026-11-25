import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    coverage = params["coverage"]

    num_areas = len(population)
    num_towers = len(tower_cost)

    model = pyo.ConcreteModel()

    model.AREAS = pyo.RangeSet(0, num_areas - 1)
    model.TOWERS = pyo.RangeSet(0, num_towers - 1)

    model.build = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.covered = pyo.Var(model.AREAS, domain=pyo.Binary)

    def coverage_rule(model, i):
        covering = [t for t in range(num_towers) if coverage[i][t] == 1]
        return model.covered[i] <= sum(model.build[t] for t in covering)

    model.coverage_con = pyo.Constraint(model.AREAS, rule=coverage_rule)

    def budget_rule(model):
        return sum(tower_cost[t] * model.build[t] for t in model.TOWERS) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    model.total_pop = pyo.Objective(
        expr=sum(population[i] * model.covered[i] for i in model.AREAS),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_pop))
    return {"objective": obj_val, "status": "optimal"}