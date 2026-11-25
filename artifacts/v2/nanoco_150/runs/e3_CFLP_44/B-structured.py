# IR: {"sets":{"clients":"1..19","facilities":"1..5"},"params":{"fixed_cost":"facility opening costs","capacity":"facility capacities","demand":"client demands","logistics_cost":"client-by-facility assignment costs"},"variables":{"opened[j]":"Binary","assigned[i,j]":"Binary"},"constraints":["For each client i: sum_j assigned[i,j] = 1","For each facility j: sum_i demand[i]*assigned[i,j] <= capacity[j]*opened[j]","For each client i and facility j: assigned[i,j] <= opened[j]"],"objective":"Minimize sum_j fixed_cost[j]*opened[j] + sum_i,j logistics_cost[i,j]*assigned[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(values, position):
    """Read a zero-based sequence or a mapping with one-based keys."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position - 1]


def _matrix_entry(values, client, facility):
    """Read a nested matrix, also accepting mappings keyed by index pairs."""
    if isinstance(values, Mapping) and (client, facility) in values:
        return values[(client, facility)]
    return _entry(_entry(values, client), facility)


def solve(params):
    model = pyo.ConcreteModel()

    model.clients = pyo.RangeSet(1, 19)
    model.facilities = pyo.RangeSet(1, 5)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda _, facility: _entry(
            params["fixed_cost"], facility
        ),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda _, facility: _entry(
            params["capacity"], facility
        ),
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.clients,
        initialize=lambda _, client: _entry(
            params["demand"], client
        ),
        within=pyo.NonNegativeReals,
    )
    model.logistics_cost = pyo.Param(
        model.clients,
        model.facilities,
        initialize=lambda _, client, facility: _matrix_entry(
            params["logistics_cost"], client, facility
        ),
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.assigned = pyo.Var(
        model.clients, model.facilities, domain=pyo.Binary
    )

    def single_source_rule(current, client):
        return sum(
            current.assigned[client, facility]
            for facility in current.facilities
        ) == 1

    model.single_source = pyo.Constraint(
        model.clients, rule=single_source_rule
    )

    def capacity_rule(current, facility):
        return sum(
            current.demand[client] * current.assigned[client, facility]
            for client in current.clients
        ) <= current.capacity[facility] * current.opened[facility]

    model.capacity_limit = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    def opening_rule(current, client, facility):
        return (
            current.assigned[client, facility]
            <= current.opened[facility]
        )

    model.opening_link = pyo.Constraint(
        model.clients, model.facilities, rule=opening_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[facility] * model.opened[facility]
                for facility in model.facilities
            )
            + sum(
                model.logistics_cost[client, facility]
                * model.assigned[client, facility]
                for client in model.clients
                for facility in model.facilities
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}