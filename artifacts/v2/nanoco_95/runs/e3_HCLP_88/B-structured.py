# IR: {"sets":{"I":"households 1..21","J":"candidate NAPs 1..15","B":"{(i,j): distance_matrix[i,j] <= basic_radius_R1}","P":"{(i,j): distance_matrix[i,j] <= premium_radius_R2}"},"params":{"installation_cost":"J -> real","client_x":"I -> real (descriptive)","client_y":"I -> real (descriptive)","facility_x":"J -> real (descriptive)","facility_y":"J -> real (descriptive)","demand":"I -> real (descriptive; no capacity constraints specified)","distance_matrix":"I x J -> real; authoritative distances","basic_radius_R1":"real","premium_radius_R2":"real","premium_bonus":"I -> real"},"variables":{"installed[j]":"binary","premium[i]":"binary"},"constraints":{"basic_coverage[i]":"sum(installed[j] for j with (i,j) in B) >= 1","premium_upper[i]":"premium[i] <= sum(installed[j] for j with (i,j) in P)","premium_lower[i,j]":"premium[i] >= installed[j] for every (i,j) in P"},"objective":"minimize sum(installation_cost[j]*installed[j] for j in J) - sum(premium_bonus[i]*premium[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _vector_entry(values, position):
    """Accept zero-based sequences or mappings keyed by one-based IDs."""
    if isinstance(values, Mapping):
        if position in values:
            return values[position]
        return values[str(position)]
    return values[position - 1]


def _matrix_entry(values, row_id, column_id):
    """Also accept matrices mapped directly by one-based (row, column) keys."""
    if isinstance(values, Mapping):
        if (row_id, column_id) in values:
            return values[row_id, column_id]
        if (str(row_id), str(column_id)) in values:
            return values[str(row_id), str(column_id)]
    return _vector_entry(_vector_entry(values, row_id), column_id)


def solve(params):
    """
    Build and solve the NAP deployment problem.

    Vector inputs may be sequences or mappings with one-based integer/string
    keys. The distance matrix may be nested sequences, nested mappings, or a
    mapping keyed by one-based (household, facility) tuples.
    """
    installation_cost = params["installation_cost"]
    client_x = params["client_x"]
    client_y = params["client_y"]
    facility_x = params["facility_x"]
    facility_y = params["facility_y"]
    demand = params["demand"]
    distance_matrix = params["distance_matrix"]
    basic_radius_R1 = params["basic_radius_R1"]
    premium_radius_R2 = params["premium_radius_R2"]
    premium_bonus = params["premium_bonus"]

    model = pyo.ConcreteModel()
    model.households = pyo.RangeSet(1, 21)
    model.facilities = pyo.RangeSet(1, 15)

    model.installation_cost = pyo.Param(
        model.facilities,
        initialize={
            site_id: _vector_entry(installation_cost, site_id)
            for site_id in model.facilities
        },
        within=pyo.Reals,
    )
    model.client_x = pyo.Param(
        model.households,
        initialize={
            client_id: _vector_entry(client_x, client_id)
            for client_id in model.households
        },
        within=pyo.Reals,
    )
    model.client_y = pyo.Param(
        model.households,
        initialize={
            client_id: _vector_entry(client_y, client_id)
            for client_id in model.households
        },
        within=pyo.Reals,
    )
    model.facility_x = pyo.Param(
        model.facilities,
        initialize={
            site_id: _vector_entry(facility_x, site_id)
            for site_id in model.facilities
        },
        within=pyo.Reals,
    )
    model.facility_y = pyo.Param(
        model.facilities,
        initialize={
            site_id: _vector_entry(facility_y, site_id)
            for site_id in model.facilities
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.households,
        initialize={
            client_id: _vector_entry(demand, client_id)
            for client_id in model.households
        },
        within=pyo.Reals,
    )
    model.distance_matrix = pyo.Param(
        model.households,
        model.facilities,
        initialize={
            (client_id, site_id): _matrix_entry(
                distance_matrix, client_id, site_id
            )
            for client_id in model.households
            for site_id in model.facilities
        },
        within=pyo.Reals,
    )
    model.basic_radius_R1 = pyo.Param(
        initialize=basic_radius_R1, within=pyo.Reals
    )
    model.premium_radius_R2 = pyo.Param(
        initialize=premium_radius_R2, within=pyo.Reals
    )
    model.premium_bonus = pyo.Param(
        model.households,
        initialize={
            client_id: _vector_entry(premium_bonus, client_id)
            for client_id in model.households
        },
        within=pyo.Reals,
    )

    basic_neighbors = {
        client_id: [
            site_id
            for site_id in model.facilities
            if pyo.value(model.distance_matrix[client_id, site_id])
            <= pyo.value(model.basic_radius_R1)
        ]
        for client_id in model.households
    }
    premium_neighbors = {
        client_id: [
            site_id
            for site_id in model.facilities
            if pyo.value(model.distance_matrix[client_id, site_id])
            <= pyo.value(model.premium_radius_R2)
        ]
        for client_id in model.households
    }

    model.basic_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (client_id, site_id)
            for client_id in model.households
            for site_id in basic_neighbors[client_id]
        ],
    )
    model.premium_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (client_id, site_id)
            for client_id in model.households
            for site_id in premium_neighbors[client_id]
        ],
    )

    model.installed = pyo.Var(model.facilities, domain=pyo.Binary)
    model.premium = pyo.Var(model.households, domain=pyo.Binary)

    def basic_coverage_rule(block, client_id):
        eligible_sites = basic_neighbors[client_id]
        if not eligible_sites:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            block.installed[site_id] for site_id in eligible_sites
        ) >= 1

    model.basic_coverage = pyo.Constraint(
        model.households, rule=basic_coverage_rule
    )

    def premium_upper_rule(block, client_id):
        return block.premium[client_id] <= pyo.quicksum(
            block.installed[site_id]
            for site_id in premium_neighbors[client_id]
        )

    model.premium_upper = pyo.Constraint(
        model.households, rule=premium_upper_rule
    )

    def premium_lower_rule(block, client_id, site_id):
        return block.premium[client_id] >= block.installed[site_id]

    model.premium_lower = pyo.Constraint(
        model.premium_pairs, rule=premium_lower_rule
    )

    model.net_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.installation_cost[site_id] * model.installed[site_id]
            for site_id in model.facilities
        )
        - pyo.quicksum(
            model.premium_bonus[client_id] * model.premium[client_id]
            for client_id in model.households
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.net_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}