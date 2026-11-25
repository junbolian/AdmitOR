# IR: {"sets":{"I":"0..26","J":"0..9","A":"{(i,j) in I x J: distance_matrix[i][j] <= coverage_threshold_km}"},"params":{"demands":"nonnegative real[I]","coverage_threshold_km":"nonnegative real","num_sites_to_deploy":"nonnegative integer","distance_matrix":"nonnegative real[I,J]"},"variables":{"selected[j]":"binary, j in J","covered[i]":"binary, i in I"},"constraints":["sum(selected[j] for j in J) == num_sites_to_deploy","covered[i] <= sum(selected[j] for j in J if (i,j) in A), for i in I","covered[i] >= selected[j], for (i,j) in A"],"objective":"maximize sum(demands[i] * covered[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = params["demands"]
    coverage_threshold_km = params["coverage_threshold_km"]
    num_sites_to_deploy = params["num_sites_to_deploy"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, 26)
    model.sites = pyo.RangeSet(0, 9)

    model.demand_units = pyo.Param(
        model.communities,
        initialize=lambda model, i: demands[i],
        within=pyo.NonNegativeReals,
    )
    model.coverage_limit = pyo.Param(
        initialize=coverage_threshold_km,
        within=pyo.NonNegativeReals,
    )
    model.deployment_count = pyo.Param(
        initialize=num_sites_to_deploy,
        within=pyo.NonNegativeIntegers,
    )
    model.travel_distance = pyo.Param(
        model.communities,
        model.sites,
        initialize=lambda model, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.coverage_pairs = pyo.Set(
        dimen=2,
        within=model.communities * model.sites,
        initialize=[
            (i, j)
            for i in model.communities
            for j in model.sites
            if pyo.value(model.travel_distance[i, j])
            <= pyo.value(model.coverage_limit)
        ],
    )

    model.selected = pyo.Var(model.sites, domain=pyo.Binary)
    model.covered = pyo.Var(model.communities, domain=pyo.Binary)

    model.exact_deployment = pyo.Constraint(
        expr=sum(model.selected[j] for j in model.sites)
        == model.deployment_count
    )

    def coverage_upper_rule(model, i):
        return model.covered[i] <= sum(
            model.selected[j]
            for j in model.sites
            if (i, j) in model.coverage_pairs
        )

    model.coverage_upper = pyo.Constraint(
        model.communities,
        rule=coverage_upper_rule,
    )

    def coverage_lower_rule(model, i, j):
        return model.covered[i] >= model.selected[j]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs,
        rule=coverage_lower_rule,
    )

    model.total_reach = pyo.Objective(
        expr=sum(
            model.demand_units[i] * model.covered[i]
            for i in model.communities
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_reach))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}