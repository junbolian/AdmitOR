# IR: {"sets":{"nodes":"0..17","sites":"0..4"},"params":{"fixed_costs":"params['fixed_costs'][j]","capacities":"params['capacities'][j]","demands":"params['demands'][i]","latency_matrix":"params['latency_matrix'][i][j]"},"metadata":{"site_coordinates":"params['site_coordinates']; fixed geometry, unused in optimization","node_coordinates":"params['node_coordinates']; fixed geometry, unused in optimization"},"variables":{"opened[j]":"binary","assigned[i,j]":"binary"},"constraints":["For each node i: sum_j assigned[i,j] = 1.","For each site j: sum_i demands[i]*assigned[i,j] <= capacities[j]*opened[j].","For each node i and site j: assigned[i,j] <= opened[j]."],"objective":"Minimize sum_j fixed_costs[j]*opened[j] + sum_i sum_j latency_matrix[i,j]*assigned[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the capacitated, single-source data center location problem.

    Inputs use zero-based sequences. The latency matrix has 18 rows and
    5 columns. Coordinates are fixed geometry and do not affect costs.
    """
    fixed_costs = params["fixed_costs"]
    capacities = params["capacities"]
    demands = params["demands"]
    latency_matrix = params["latency_matrix"]
    site_coordinates = params["site_coordinates"]
    node_coordinates = params["node_coordinates"]

    if len(fixed_costs) != 5 or len(capacities) != 5:
        raise ValueError("fixed_costs and capacities must each have length 5.")
    if len(demands) != 18:
        raise ValueError("demands must have length 18.")
    if len(latency_matrix) != 18 or any(
        len(row) != 5 for row in latency_matrix
    ):
        raise ValueError("latency_matrix must have shape 18 by 5.")
    if len(site_coordinates) != 5 or any(
        len(point) != 2 for point in site_coordinates
    ):
        raise ValueError("site_coordinates must have shape 5 by 2.")
    if len(node_coordinates) != 18 or any(
        len(point) != 2 for point in node_coordinates
    ):
        raise ValueError("node_coordinates must have shape 18 by 2.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 17)
    model.sites = pyo.RangeSet(0, 4)

    model.fixed_cost = pyo.Param(
        model.sites,
        initialize={j: fixed_costs[j] for j in model.sites},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.sites,
        initialize={j: capacities[j] for j in model.sites},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.nodes,
        initialize={i: demands[i] for i in model.nodes},
        within=pyo.NonNegativeReals,
    )
    model.latency = pyo.Param(
        model.nodes,
        model.sites,
        initialize={
            (i, j): latency_matrix[i][j]
            for i in model.nodes
            for j in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.sites, domain=pyo.Binary)
    model.assigned = pyo.Var(model.nodes, model.sites, domain=pyo.Binary)

    def single_source_rule(instance, i):
        return sum(instance.assigned[i, j] for j in instance.sites) == 1

    model.single_source = pyo.Constraint(
        model.nodes, rule=single_source_rule
    )

    def capacity_rule(instance, j):
        return (
            sum(
                instance.demand[i] * instance.assigned[i, j]
                for i in instance.nodes
            )
            <= instance.capacity[j] * instance.opened[j]
        )

    model.capacity_limit = pyo.Constraint(
        model.sites, rule=capacity_rule
    )

    def opening_rule(instance, i, j):
        return instance.assigned[i, j] <= instance.opened[j]

    model.opening_link = pyo.Constraint(
        model.nodes, model.sites, rule=opening_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[j] * model.opened[j]
                for j in model.sites
            )
            + sum(
                model.latency[i, j] * model.assigned[i, j]
                for i in model.nodes
                for j in model.sites
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when automatic solution loading fails
        # because no feasible solution is available.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}