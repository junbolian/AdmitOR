# IR: {"sets":{"N":"0..19","J":"0..13","S_i":"{j in J: distance_matrix[i,j] <= R1_safe_range}","U_i":"{j in J: distance_matrix[i,j] <= R2_ultra_range}"},"params":{"construction_costs":"real[J]","node_demands":"nonnegative[N], informational; all nodes require coverage","bonus_values":"real[N]","R1_safe_range":"nonnegative scalar","R2_ultra_range":"nonnegative scalar","distance_matrix":"nonnegative[N,J]"},"variables":{"site_open[j]":"binary","ultra_access[i]":"binary"},"constraints":["sum(site_open[j] for j in S_i) >= 1 for each i in N","ultra_access[i] <= sum(site_open[j] for j in U_i) for each i in N","ultra_access[i] >= site_open[j] for each i in N and j in U_i"],"objective":"minimize sum(construction_costs[j]*site_open[j] for j in J) - sum(bonus_values[i]*ultra_access[i] for i in N)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based, node-by-site input sequences."""
    construction_costs = params["construction_costs"]
    node_demands = params["node_demands"]
    bonus_values = params["bonus_values"]
    safe_range = params["R1_safe_range"]
    ultra_range = params["R2_ultra_range"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.driver_nodes = pyo.RangeSet(0, 19)
    model.candidate_sites = pyo.RangeSet(0, 13)

    model.construction_costs = pyo.Param(
        model.candidate_sites,
        initialize=lambda model, site: construction_costs[site],
        within=pyo.Reals,
    )
    model.node_demands = pyo.Param(
        model.driver_nodes,
        initialize=lambda model, node: node_demands[node],
        within=pyo.NonNegativeReals,
    )
    model.bonus_values = pyo.Param(
        model.driver_nodes,
        initialize=lambda model, node: bonus_values[node],
        within=pyo.Reals,
    )
    model.safe_radius = pyo.Param(
        initialize=safe_range, within=pyo.NonNegativeReals
    )
    model.ultra_radius = pyo.Param(
        initialize=ultra_range, within=pyo.NonNegativeReals
    )
    model.travel_distance = pyo.Param(
        model.driver_nodes,
        model.candidate_sites,
        initialize=lambda model, node, site: distance_matrix[node][site],
        within=pyo.NonNegativeReals,
    )

    model.safe_neighbors = pyo.Set(
        model.driver_nodes,
        within=model.candidate_sites,
        initialize=lambda model, node: [
            site
            for site in model.candidate_sites
            if pyo.value(model.travel_distance[node, site])
            <= pyo.value(model.safe_radius)
        ],
    )
    model.ultra_neighbors = pyo.Set(
        model.driver_nodes,
        within=model.candidate_sites,
        initialize=lambda model, node: [
            site
            for site in model.candidate_sites
            if pyo.value(model.travel_distance[node, site])
            <= pyo.value(model.ultra_radius)
        ],
    )
    model.ultra_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (node, site)
            for node in model.driver_nodes
            for site in model.ultra_neighbors[node]
        ],
    )

    model.site_open = pyo.Var(model.candidate_sites, domain=pyo.Binary)
    model.ultra_access = pyo.Var(model.driver_nodes, domain=pyo.Binary)

    def safe_coverage_rule(model, node):
        # The tuple also represents infeasibility when the neighbor set is empty.
        return (
            1,
            pyo.quicksum(
                model.site_open[site] for site in model.safe_neighbors[node]
            ),
            None,
        )

    model.safe_coverage = pyo.Constraint(
        model.driver_nodes, rule=safe_coverage_rule
    )

    model.ultra_access_upper = pyo.Constraint(
        model.driver_nodes,
        rule=lambda model, node: model.ultra_access[node]
        <= pyo.quicksum(
            model.site_open[site] for site in model.ultra_neighbors[node]
        ),
    )

    model.ultra_access_lower = pyo.Constraint(
        model.ultra_pairs,
        rule=lambda model, node, site: (
            model.ultra_access[node] >= model.site_open[site]
        ),
    )

    model.net_deployment_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.construction_costs[site] * model.site_open[site]
            for site in model.candidate_sites
        )
        - pyo.quicksum(
            model.bonus_values[node] * model.ultra_access[node]
            for node in model.driver_nodes
        ),
        sense=pyo.minimize,
    )

    # APPsi HiGHS may raise RuntimeError when no solution can be loaded.
    # Objective retrievability alone determines whether success is returned.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.net_deployment_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}