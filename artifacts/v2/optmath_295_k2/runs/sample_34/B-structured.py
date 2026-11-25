# IR: {"sets":{"A":"range(params['num_areas'])","T":"range(params['num_towers'])"},"params":{"populations":"nonnegative population[A]","tower_costs":"nonnegative cost[T]","budget":"real budget limit","coverage_links":"binary incidence[A,T]","num_areas":"size of A","num_towers":"size of T"},"variables":{"build[T]":"binary","covered[A]":"binary"},"constraints":["sum(tower_costs[j]*build[j] for j in T) <= budget","covered[i] <= sum(coverage_links[i,j]*build[j] for j in T), for each i in A"],"objective":"maximize sum(populations[i]*covered[i] for i in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    coverage_links = params["coverage_links"]
    num_areas = params["num_areas"]
    num_towers = params["num_towers"]

    model = pyo.ConcreteModel()

    model.areas = pyo.Set(initialize=range(num_areas), ordered=True)
    model.towers = pyo.Set(initialize=range(num_towers), ordered=True)

    model.population = pyo.Param(
        model.areas,
        initialize=lambda mdl, area: populations[area],
        within=pyo.NonNegativeReals,
    )
    model.construction_cost = pyo.Param(
        model.towers,
        initialize=lambda mdl, tower: tower_costs[tower],
        within=pyo.NonNegativeReals,
    )
    model.budget_limit = pyo.Param(
        initialize=budget,
        within=pyo.Reals,
    )
    model.coverage_incidence = pyo.Param(
        model.areas,
        model.towers,
        initialize=lambda mdl, area, tower: coverage_links[area][tower],
        within=pyo.Binary,
    )

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=(
            None,
            pyo.quicksum(
                model.construction_cost[tower] * model.build[tower]
                for tower in model.towers
            ),
            model.budget_limit,
        )
    )

    def coverage_rule(mdl, area):
        return mdl.covered[area] <= pyo.quicksum(
            mdl.coverage_incidence[area, tower] * mdl.build[tower]
            for tower in mdl.towers
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )

    model.total_population = pyo.Objective(
        expr=pyo.quicksum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}