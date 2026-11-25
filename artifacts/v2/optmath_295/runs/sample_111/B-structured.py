# IR: {"sets":{"towers":"0..7","areas":"0..10","serves":{"0":[3],"1":[0,1,2,3,7],"2":[1,2,6],"3":[0,4,5,6],"4":[3,5],"5":[3,5],"6":[0,3,4],"7":[2,3,4,5],"8":[2,4,5],"9":[2,5],"10":[1,2,3,4,5]}},"params":{"budget":"params['budget']","population[a]":"params['population'][a]","tower_cost[t]":"params['tower_cost'][t]"},"variables":{"build[t]":"Binary","covered[a]":"Binary"},"constraints":["sum(tower_cost[t]*build[t] for t in towers) <= budget","covered[a] <= sum(build[t] for t in serves[a]) for each area a","covered[a] >= build[t] for each area a and tower t in serves[a]"],"objective":"maximize sum(population[a]*covered[a] for a in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using population and tower_cost sequences or integer-keyed mappings."""
    budget = params["budget"]
    population = params["population"]
    tower_cost = params["tower_cost"]

    serves = {
        0: (3,),
        1: (0, 1, 2, 3, 7),
        2: (1, 2, 6),
        3: (0, 4, 5, 6),
        4: (3, 5),
        5: (3, 5),
        6: (0, 3, 4),
        7: (2, 3, 4, 5),
        8: (2, 4, 5),
        9: (2, 5),
        10: (1, 2, 3, 4, 5),
    }

    model = pyo.ConcreteModel()
    model.towers = pyo.RangeSet(0, 7)
    model.areas = pyo.RangeSet(0, 10)
    model.coverage_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (area, tower)
            for area, towers in serves.items()
            for tower in towers
        ],
    )

    model.budget = pyo.Param(initialize=budget)
    model.population = pyo.Param(
        model.areas,
        initialize={area: population[area] for area in model.areas},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in model.towers},
    )

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    def coverage_upper_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.build[tower] for tower in serves[area]
        )

    model.coverage_upper = pyo.Constraint(
        model.areas, rule=coverage_upper_rule
    )

    def coverage_lower_rule(instance, area, tower):
        return instance.covered[area] >= instance.build[tower]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs, rule=coverage_lower_rule
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}