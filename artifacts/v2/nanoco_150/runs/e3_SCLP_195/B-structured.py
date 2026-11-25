# IR: {"sets":{"Z":"range(params['num_zones'])","S":"range(params['num_sites'])"},"params":{"num_zones":"number of zones","num_sites":"number of sites","site_costs":"cost[j] for j in S","coverage_radius":"maximum covered distance","zone_site_distances":"distance[i][j] for i in Z, j in S"},"variables":{"install[j]":"Binary for j in S"},"constraints":["coverage[i]: sum(install[j] for j in S if distance[i][j] <= coverage_radius) >= 1 for i in Z"],"objective":"minimize sum(cost[j] * install[j] for j in S)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the locker set-covering problem using zero-based input arrays."""
    num_zones = params["num_zones"]
    num_sites = params["num_sites"]
    site_costs = params["site_costs"]
    coverage_radius = params["coverage_radius"]
    zone_site_distances = params["zone_site_distances"]

    model = pyo.ConcreteModel()

    model.Z = pyo.Set(initialize=range(num_zones), ordered=True)
    model.S = pyo.Set(initialize=range(num_sites), ordered=True)

    model.site_cost = pyo.Param(
        model.S,
        initialize={j: site_costs[j] for j in range(num_sites)},
        within=pyo.Reals,
    )
    model.radius = pyo.Param(
        initialize=coverage_radius,
        within=pyo.NonNegativeReals,
    )
    model.distance = pyo.Param(
        model.Z,
        model.S,
        initialize={
            (i, j): zone_site_distances[i][j]
            for i in range(num_zones)
            for j in range(num_sites)
        },
        within=pyo.NonNegativeReals,
    )

    model.install = pyo.Var(model.S, domain=pyo.Binary)

    def coverage_rule(instance, i):
        eligible_sites = [
            j
            for j in instance.S
            if pyo.value(instance.distance[i, j])
            <= pyo.value(instance.radius)
        ]
        # Tuple form also represents an infeasible empty coverage row safely.
        return (
            1,
            pyo.quicksum(instance.install[j] for j in eligible_sites),
            None,
        )

    model.coverage = pyo.Constraint(model.Z, rule=coverage_rule)

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.site_cost[j] * model.install[j] for j in model.S
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}