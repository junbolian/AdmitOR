# IR: {"sets":{"I":"1..21 households","J":"1..15 candidate facilities","K":"{0,1} coordinate axes","B[i]":"{j: distance_matrix[i,j] <= basic_coverage_radius_R1}","P[i]":"{j: distance_matrix[i,j] <= premium_coverage_radius_R2}"},"params":{"facility_installation_cost":"J -> real","client_demand":"I -> real; metadata only, no capacity constraints specified","client_premium_bonus":"I -> real","basic_coverage_radius_R1":"real","premium_coverage_radius_R2":"real","household_coordinates":"I x K -> real; metadata only, supplied distances govern coverage","facility_coordinates":"J x K -> real; metadata only, supplied distances govern coverage","distance_matrix":"I x J -> real"},"variables":{"installed[j]":"binary","premium[i]":"binary"},"constraints":["For each i: sum(installed[j] for j in B[i]) >= 1","For each i: premium[i] <= sum(installed[j] for j in P[i])","For each i and j in P[i]: premium[i] >= installed[j]"],"objective":"minimize sum(facility_installation_cost[j]*installed[j] for j in J) - sum(client_premium_bonus[i]*premium[i] for i in I)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Indexed inputs accept ordinary zero-based Python sequences or mappings
    keyed by one-based integer IDs (or their string representations).

    Coordinates contain (x, y) pairs. The distance matrix accepts nested
    rows or a mapping keyed by (household_id, facility_id) tuples.
    """

    def indexed(data, identifier):
        if isinstance(data, Mapping):
            if identifier in data:
                return data[identifier]
            return data[str(identifier)]
        return data[identifier - 1]

    def matrix_entry(data, household_id, facility_id):
        if isinstance(data, Mapping):
            pair = (household_id, facility_id)
            if pair in data:
                return data[pair]
        return indexed(indexed(data, household_id), facility_id)

    household_ids = range(1, 22)
    facility_ids = range(1, 16)
    coordinate_axes = (0, 1)

    raw_costs = params["facility_installation_cost"]
    raw_demands = params["client_demand"]
    raw_bonuses = params["client_premium_bonus"]
    basic_radius = float(params["basic_coverage_radius_R1"])
    premium_radius = float(params["premium_coverage_radius_R2"])
    raw_household_coordinates = params["household_coordinates"]
    raw_facility_coordinates = params["facility_coordinates"]
    raw_distances = params["distance_matrix"]

    costs = {
        facility_id: float(indexed(raw_costs, facility_id))
        for facility_id in facility_ids
    }
    demands = {
        household_id: float(indexed(raw_demands, household_id))
        for household_id in household_ids
    }
    bonuses = {
        household_id: float(indexed(raw_bonuses, household_id))
        for household_id in household_ids
    }
    household_coordinates = {
        (household_id, axis): float(
            indexed(raw_household_coordinates, household_id)[axis]
        )
        for household_id in household_ids
        for axis in coordinate_axes
    }
    facility_coordinates = {
        (facility_id, axis): float(
            indexed(raw_facility_coordinates, facility_id)[axis]
        )
        for facility_id in facility_ids
        for axis in coordinate_axes
    }
    distances = {
        (household_id, facility_id): float(
            matrix_entry(raw_distances, household_id, facility_id)
        )
        for household_id in household_ids
        for facility_id in facility_ids
    }

    basic_neighbors = {
        household_id: [
            facility_id
            for facility_id in facility_ids
            if distances[household_id, facility_id] <= basic_radius
        ]
        for household_id in household_ids
    }
    premium_neighbors = {
        household_id: [
            facility_id
            for facility_id in facility_ids
            if distances[household_id, facility_id] <= premium_radius
        ]
        for household_id in household_ids
    }

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(1, 21)
    model.J = pyo.RangeSet(1, 15)
    model.K = pyo.Set(initialize=coordinate_axes, ordered=True)

    model.facility_installation_cost = pyo.Param(model.J, initialize=costs)
    model.client_demand = pyo.Param(model.I, initialize=demands)
    model.client_premium_bonus = pyo.Param(model.I, initialize=bonuses)
    model.basic_coverage_radius_R1 = pyo.Param(initialize=basic_radius)
    model.premium_coverage_radius_R2 = pyo.Param(initialize=premium_radius)
    model.household_coordinates = pyo.Param(
        model.I, model.K, initialize=household_coordinates
    )
    model.facility_coordinates = pyo.Param(
        model.J, model.K, initialize=facility_coordinates
    )
    model.distance_matrix = pyo.Param(
        model.I, model.J, initialize=distances
    )

    model.B = pyo.Set(
        model.I, within=model.J, initialize=basic_neighbors
    )
    model.P = pyo.Set(
        model.I, within=model.J, initialize=premium_neighbors
    )

    model.installed = pyo.Var(model.J, domain=pyo.Binary)
    model.premium = pyo.Var(model.I, domain=pyo.Binary)

    def basic_coverage_rule(network, household_id):
        if len(network.B[household_id]) == 0:
            return pyo.Constraint.Infeasible
        return sum(
            network.installed[facility_id]
            for facility_id in network.B[household_id]
        ) >= 1

    model.basic_coverage = pyo.Constraint(
        model.I, rule=basic_coverage_rule
    )

    def premium_upper_rule(network, household_id):
        return network.premium[household_id] <= sum(
            network.installed[facility_id]
            for facility_id in network.P[household_id]
        )

    model.premium_upper = pyo.Constraint(
        model.I, rule=premium_upper_rule
    )

    model.premium_lower = pyo.Constraint(
        [
            (household_id, facility_id)
            for household_id in household_ids
            for facility_id in premium_neighbors[household_id]
        ],
        rule=lambda network, household_id, facility_id: (
            network.premium[household_id]
            >= network.installed[facility_id]
        ),
    )

    model.net_cost = pyo.Objective(
        expr=sum(
            model.facility_installation_cost[facility_id]
            * model.installed[facility_id]
            for facility_id in model.J
        )
        - sum(
            model.client_premium_bonus[household_id]
            * model.premium[household_id]
            for household_id in model.I
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_error"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.net_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}