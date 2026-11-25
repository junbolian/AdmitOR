# IR: {"sets":{"A":"range(params['num_areas'])","T":"range(params['num_towers'])"},"params":{"populations":"params['populations'][a]","tower_costs":"params['tower_costs'][t]","budget":"params['budget']","coverage_links":"params['coverage_links'][a][t], fixed binary incidence","num_areas":"params['num_areas']","num_towers":"params['num_towers']"},"variables":{"build[t]":"Binary, t in T","covered[a]":"Binary, a in A"},"constraints":["sum(tower_costs[t]*build[t] for t in T) <= budget","covered[a] <= sum(coverage_links[a][t]*build[t] for t in T), a in A"],"objective":"maximize sum(populations[a]*covered[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_areas = params["num_areas"]
    num_towers = params["num_towers"]
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    coverage_links = params["coverage_links"]

    model = pyo.ConcreteModel()

    model.areas = pyo.Set(initialize=range(num_areas), ordered=True)
    model.towers = pyo.Set(initialize=range(num_towers), ordered=True)

    model.population = pyo.Param(
        model.areas,
        initialize=lambda mdl, a: populations[a],
        within=pyo.NonNegativeReals,
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize=lambda mdl, t: tower_costs[t],
        within=pyo.NonNegativeReals,
    )
    model.budget_limit = pyo.Param(
        initialize=budget,
        within=pyo.Reals,
    )
    model.coverage_incidence = pyo.Param(
        model.areas,
        model.towers,
        initialize=lambda mdl, a, t: coverage_links[a][t],
        within=pyo.Binary,
        mutable=False,
    )

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.construction_budget = pyo.Constraint(
        expr=sum(
            model.tower_cost[t] * model.build[t]
            for t in model.towers
        ) <= model.budget_limit
    )

    def coverage_rule(mdl, a):
        return mdl.covered[a] <= sum(
            mdl.coverage_incidence[a, t] * mdl.build[t]
            for t in mdl.towers
        )

    model.coverage_requirement = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[a] * model.covered[a]
            for a in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}