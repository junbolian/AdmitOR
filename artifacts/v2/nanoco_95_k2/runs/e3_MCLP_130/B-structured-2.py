# IR: {"sets":{"I":"0..26","J":"0..9","A":"{(i,j) in I x J: distance_matrix[i,j] <= coverage_threshold_km}"},"params":{"demands":"nonnegative real[I]","coverage_threshold_km":"nonnegative real","num_sites_to_deploy":"nonnegative integer","distance_matrix":"nonnegative real[I,J]"},"variables":{"deploy[j]":"binary, j in J","covered[i]":"binary, i in I"},"constraints":["sum(deploy[j] for j in J) = num_sites_to_deploy","covered[i] <= sum(deploy[j] for j in J if (i,j) in A), for each i in I","covered[i] >= deploy[j], for each (i,j) in A"],"objective":"maximize sum(demands[i] * covered[i] for i in I)"}

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

    model.demands = pyo.Param(
        model.communities,
        initialize={i: demands[i] for i in model.communities},
        within=pyo.NonNegativeReals,
    )
    model.coverage_threshold_km = pyo.Param(
        initialize=coverage_threshold_km,
        within=pyo.NonNegativeReals,
    )
    model.num_sites_to_deploy = pyo.Param(
        initialize=num_sites_to_deploy,
        within=pyo.NonNegativeIntegers,
    )
    model.distance_matrix = pyo.Param(
        model.communities,
        model.sites,
        initialize={
            (i, j): distance_matrix[i][j]
            for i in model.communities
            for j in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    model.coverage_pairs = pyo.Set(
        dimen=2,
        within=model.communities * model.sites,
        initialize=[
            (i, j)
            for i in model.communities
            for j in model.sites
            if pyo.value(model.distance_matrix[i, j])
            <= pyo.value(model.coverage_threshold_km)
        ],
    )

    model.deploy = pyo.Var(model.sites, domain=pyo.Binary)
    model.covered = pyo.Var(model.communities, domain=pyo.Binary)

    model.deployment_count = pyo.Constraint(
        expr=sum(model.deploy[j] for j in model.sites)
        == model.num_sites_to_deploy
    )

    def coverage_upper_rule(model, i):
        return model.covered[i] <= sum(
            model.deploy[j]
            for j in model.sites
            if (i, j) in model.coverage_pairs
        )

    model.coverage_upper = pyo.Constraint(
        model.communities, rule=coverage_upper_rule
    )

    def coverage_lower_rule(model, i, j):
        return model.covered[i] >= model.deploy[j]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs, rule=coverage_lower_rule
    )

    model.total_reach = pyo.Objective(
        expr=sum(
            model.demands[i] * model.covered[i]
            for i in model.communities
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors propagate to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_reach))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}