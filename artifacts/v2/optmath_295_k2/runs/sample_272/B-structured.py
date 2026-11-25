# IR: {"sets":{"areas":"0..8","towers":"0..8","serves":{"0":[2,4,5,6,7],"1":[0,1,6,8],"2":[1,6,8],"3":[1,2,6,7],"4":[0,2,3,6,7,8],"5":[0,1,2,6,7],"6":[0,1,2,4],"7":[1,2,4,5,6],"8":[0,1,3,4,5,8]}},"params":{"population":"area-indexed input","tower_cost":"tower-indexed input","budget":"scalar input"},"variables":{"build[t]":"binary","covered[a]":"binary"},"constraints":["covered[a] <= sum(build[t] for t in serves[a]) for each area a","sum(tower_cost[t]*build[t] for t in towers) <= budget"],"objective":"maximize sum(population[a]*covered[a] for a in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    serves = {
        0: (2, 4, 5, 6, 7),
        1: (0, 1, 6, 8),
        2: (1, 6, 8),
        3: (1, 2, 6, 7),
        4: (0, 2, 3, 6, 7, 8),
        5: (0, 1, 2, 6, 7),
        6: (0, 1, 2, 4),
        7: (1, 2, 4, 5, 6),
        8: (0, 1, 3, 4, 5, 8),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 8)
    model.towers = pyo.RangeSet(0, 8)

    model.population = pyo.Param(
        model.areas, initialize={a: population[a] for a in range(9)}
    )
    model.tower_cost = pyo.Param(
        model.towers, initialize={t: tower_cost[t] for t in range(9)}
    )
    model.budget = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.build[t] for t in serves[area]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[t] * model.build[t] for t in model.towers
        ) <= model.budget
    )
    model.total_coverage = pyo.Objective(
        expr=sum(
            model.population[a] * model.covered[a] for a in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}