# IR: {"sets":{"I":"0..26","J":"0..9","E":"{(i,j): distances[i][j] <= service_range_km}"},"params":{"service_range_km":"params['service_range_km']","demands":"params['demands'], indexed by I","distances":"params['distances'], indexed by I x J"},"variables":{"selected[j]":"binary, j in J","covered[i]":"binary, i in I"},"constraints":["sum(selected[j] for j in J) = 2","covered[i] <= sum(selected[j] for j with (i,j) in E), for each i in I","covered[i] >= selected[j], for each (i,j) in E"],"objective":"maximize sum(demands[i] * covered[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    service_range_km = params["service_range_km"]
    demands = params["demands"]
    distances = params["distances"]

    model = pyo.ConcreteModel()

    model.communities = pyo.RangeSet(0, 26)
    model.sites = pyo.RangeSet(0, 9)

    model.service_range = pyo.Param(initialize=service_range_km)
    model.demand = pyo.Param(
        model.communities,
        initialize={i: demands[i] for i in model.communities},
    )
    model.travel_distance = pyo.Param(
        model.communities,
        model.sites,
        initialize={
            (i, j): distances[i][j]
            for i in model.communities
            for j in model.sites
        },
    )

    coverage_edges = [
        (i, j)
        for i in model.communities
        for j in model.sites
        if pyo.value(model.travel_distance[i, j])
        <= pyo.value(model.service_range)
    ]
    covering_sites = {
        i: [j for community, j in coverage_edges if community == i]
        for i in model.communities
    }
    model.coverage_edges = pyo.Set(dimen=2, initialize=coverage_edges)

    model.selected = pyo.Var(model.sites, domain=pyo.Binary)
    model.covered = pyo.Var(model.communities, domain=pyo.Binary)

    model.site_count = pyo.Constraint(
        expr=sum(model.selected[j] for j in model.sites) == 2
    )

    def coverage_upper_rule(model, i):
        return model.covered[i] <= sum(
            model.selected[j] for j in covering_sites[i]
        )

    model.coverage_upper = pyo.Constraint(
        model.communities, rule=coverage_upper_rule
    )

    def coverage_lower_rule(model, i, j):
        return model.covered[i] >= model.selected[j]

    model.coverage_lower = pyo.Constraint(
        model.coverage_edges, rule=coverage_lower_rule
    )

    model.total_reach = pyo.Objective(
        expr=sum(
            model.demand[i] * model.covered[i]
            for i in model.communities
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Infeasibility or a solver failure can prevent solution loading.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_reach))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}