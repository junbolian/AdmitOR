# IR: {"sets":{"C":"0..27","S":"0..9","A":"{(i,j) in C x S: distance_matrix[i][j] <= service_radius_km}"},"params":{"num_towers_to_select":"params['num_towers_to_select']","service_radius_km":"params['service_radius_km']","community_demands":"params['community_demands'] indexed by C","distance_matrix":"params['distance_matrix'] indexed by C x S"},"variables":{"tower_active[j]":"binary, j in S","connected[i]":"binary, i in C"},"constraints":["sum(j in S, tower_active[j]) = num_towers_to_select","connected[i] <= sum(j: (i,j) in A, tower_active[j]) for i in C","connected[i] >= tower_active[j] for (i,j) in A"],"objective":"maximize sum(i in C, community_demands[i] * connected[i])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    tower_count = params["num_towers_to_select"]
    service_radius = params["service_radius_km"]
    demands = params["community_demands"]
    distances = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, 27)
    model.S = pyo.RangeSet(0, 9)

    model.num_towers_to_select = pyo.Param(initialize=tower_count)
    model.service_radius_km = pyo.Param(initialize=service_radius)
    model.community_demands = pyo.Param(
        model.C,
        initialize=lambda mdl, community: demands[community],
    )
    model.distance_matrix = pyo.Param(
        model.C,
        model.S,
        initialize=lambda mdl, community, site: distances[community][site],
    )

    model.A = pyo.Set(
        dimen=2,
        within=model.C * model.S,
        initialize=[
            (community, site)
            for community in model.C
            for site in model.S
            if distances[community][site] <= service_radius
        ],
    )

    reachable_sites = {
        community: [
            site for site in model.S if (community, site) in model.A
        ]
        for community in model.C
    }

    model.tower_active = pyo.Var(model.S, domain=pyo.Binary)
    model.connected = pyo.Var(model.C, domain=pyo.Binary)

    model.tower_cardinality = pyo.Constraint(
        expr=sum(model.tower_active[site] for site in model.S)
        == model.num_towers_to_select
    )

    def coverage_upper_rule(mdl, community):
        return mdl.connected[community] <= sum(
            mdl.tower_active[site] for site in reachable_sites[community]
        )

    model.coverage_upper = pyo.Constraint(
        model.C,
        rule=coverage_upper_rule,
    )

    def coverage_lower_rule(mdl, community, site):
        return mdl.connected[community] >= mdl.tower_active[site]

    model.coverage_lower = pyo.Constraint(
        model.A,
        rule=coverage_lower_rule,
    )

    model.total_connectivity = pyo.Objective(
        expr=sum(
            model.community_demands[community] * model.connected[community]
            for community in model.C
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_connectivity))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}