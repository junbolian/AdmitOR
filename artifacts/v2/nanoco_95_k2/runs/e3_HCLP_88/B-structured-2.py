# IR: {"sets":{"I":"1..21 households","J":"1..15 facilities","K":"0..1 coordinate axes","B":"{(i,j): distance_matrix[i,j] <= basic_coverage_radius_R1}","P":"{(i,j): distance_matrix[i,j] <= premium_coverage_radius_R2}"},"params":{"facility_installation_cost":"J -> nonnegative real","client_demand":"I -> nonnegative real; metadata, no capacity constraints specified","client_premium_bonus":"I -> real","basic_coverage_radius_R1":"nonnegative real","premium_coverage_radius_R2":"nonnegative real","household_coordinates":"I x K -> real; metadata, supplied distances govern coverage","facility_coordinates":"J x K -> real; metadata, supplied distances govern coverage","distance_matrix":"I x J -> nonnegative real"},"variables":{"installed[j]":"binary","premium[i]":"binary"},"constraints":["For every i: sum(installed[j] for (i,j) in B) >= 1.","For every i: premium[i] <= sum(installed[j] for (i,j) in P).","For every (i,j) in P: premium[i] >= installed[j]."],"objective":"Minimize sum(facility_installation_cost[j]*installed[j] for j in J) - sum(client_premium_bonus[i]*premium[i] for i in I)."}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed(data, position):
    """Accept a positional sequence or a mapping keyed by 1-based indices."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def _distance(data, household, facility):
    """Accept nested indexed data or a mapping keyed by (household, facility)."""
    if isinstance(data, Mapping) and (household, facility) in data:
        return data[household, facility]
    return _indexed(_indexed(data, household), facility)


def solve(params):
    installation_data = params["facility_installation_cost"]
    demand_data = params["client_demand"]
    bonus_data = params["client_premium_bonus"]
    basic_radius = params["basic_coverage_radius_R1"]
    premium_radius = params["premium_coverage_radius_R2"]
    household_coordinate_data = params["household_coordinates"]
    facility_coordinate_data = params["facility_coordinates"]
    distance_data = params["distance_matrix"]

    model = pyo.ConcreteModel()
    model.households = pyo.RangeSet(1, 21)
    model.facilities = pyo.RangeSet(1, 15)
    model.coordinate_axes = pyo.RangeSet(0, 1)

    model.installation_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, facility: _indexed(installation_data, facility),
        within=pyo.NonNegativeReals,
    )
    model.bandwidth_demand = pyo.Param(
        model.households,
        initialize=lambda mdl, household: _indexed(demand_data, household),
        within=pyo.NonNegativeReals,
    )
    model.premium_bonus = pyo.Param(
        model.households,
        initialize=lambda mdl, household: _indexed(bonus_data, household),
        within=pyo.Reals,
    )
    model.basic_radius = pyo.Param(
        initialize=basic_radius,
        within=pyo.NonNegativeReals,
    )
    model.premium_radius = pyo.Param(
        initialize=premium_radius,
        within=pyo.NonNegativeReals,
    )
    model.household_location = pyo.Param(
        model.households,
        model.coordinate_axes,
        initialize=lambda mdl, household, axis: _indexed(
            household_coordinate_data, household
        )[axis],
        within=pyo.Reals,
    )
    model.facility_location = pyo.Param(
        model.facilities,
        model.coordinate_axes,
        initialize=lambda mdl, facility, axis: _indexed(
            facility_coordinate_data, facility
        )[axis],
        within=pyo.Reals,
    )
    model.distance = pyo.Param(
        model.households,
        model.facilities,
        initialize=lambda mdl, household, facility: _distance(
            distance_data, household, facility
        ),
        within=pyo.NonNegativeReals,
    )

    model.basic_pairs = pyo.Set(
        dimen=2,
        within=model.households * model.facilities,
        initialize=[
            (household, facility)
            for household in model.households
            for facility in model.facilities
            if pyo.value(model.distance[household, facility])
            <= pyo.value(model.basic_radius)
        ],
    )
    model.premium_pairs = pyo.Set(
        dimen=2,
        within=model.households * model.facilities,
        initialize=[
            (household, facility)
            for household in model.households
            for facility in model.facilities
            if pyo.value(model.distance[household, facility])
            <= pyo.value(model.premium_radius)
        ],
    )

    model.installed = pyo.Var(model.facilities, domain=pyo.Binary)
    model.premium = pyo.Var(model.households, domain=pyo.Binary)

    def basic_coverage_rule(mdl, household):
        eligible_sites = [
            facility
            for facility in mdl.facilities
            if (household, facility) in mdl.basic_pairs
        ]
        if not eligible_sites:
            return pyo.Constraint.Infeasible
        return sum(mdl.installed[facility] for facility in eligible_sites) >= 1

    model.basic_coverage = pyo.Constraint(
        model.households,
        rule=basic_coverage_rule,
    )

    def premium_upper_rule(mdl, household):
        return mdl.premium[household] <= sum(
            mdl.installed[facility]
            for facility in mdl.facilities
            if (household, facility) in mdl.premium_pairs
        )

    model.premium_upper = pyo.Constraint(
        model.households,
        rule=premium_upper_rule,
    )
    model.premium_lower = pyo.Constraint(
        model.premium_pairs,
        rule=lambda mdl, household, facility: (
            mdl.premium[household] >= mdl.installed[facility]
        ),
    )

    model.net_cost = pyo.Objective(
        expr=sum(
            model.installation_cost[facility] * model.installed[facility]
            for facility in model.facilities
        )
        - sum(
            model.premium_bonus[household] * model.premium[household]
            for household in model.households
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.net_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}