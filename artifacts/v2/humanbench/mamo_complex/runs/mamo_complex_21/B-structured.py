# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j}","T":"1..7","E":"{(0,j):j=1..8} union {(7,3),(3,8)}"},"params":{"capacity_0_1":"params[\"capacity_0_1\"]","capacity_0_2":"params[\"capacity_0_2\"]","capacity_0_3":"params[\"capacity_0_3\"]","capacity_0_4":"params[\"capacity_0_4\"]","capacity_0_5":"params[\"capacity_0_5\"]","capacity_0_6":"params[\"capacity_0_6\"]","capacity_0_7":"params[\"capacity_0_7\"]","capacity_0_8":"params[\"capacity_0_8\"]","max_capacity_from_1":"params[\"max_capacity_from_1\"]","max_capacity_from_2":"params[\"max_capacity_from_2\"]","capacity_7_3":"params[\"capacity_7_3\"]","max_capacity_to_8":"params[\"max_capacity_to_8\"]","capacity_3_8":"params[\"capacity_3_8\"]"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["flow[i,j] <= supplied capacity_i_j for (i,j) in E","flow[1,j] <= max_capacity_from_1 for j != 1","flow[2,j] <= max_capacity_from_2 for j != 2","flow[i,8] <= max_capacity_to_8 for i != 8","sum_{i != k} flow[i,k] = sum_{j != k} flow[k,j] for k in T"],"objective":"maximize sum_{j != 0} flow[0,j] - sum_{i != 0} flow[i,0]","interpretation":"All distinct station pairs are potential directed links. Apply every supplied capacity bound; otherwise impose no additional link bound. This computes an optimistic maximum under the supplied bounds, not an identifiable maximum for an omitted fixed capacity matrix."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The description omits individual capacities for many links.
    # To use only the listed parameters, solve the upper-bound network
    # defined in the IR. Missing capacities are not assumed to be zero.
    # Overlapping bounds all apply, including bounds on links into Station 8.

    source_capacities = {
        destination: float(params[f"capacity_0_{destination}"])
        for destination in range(1, 9)
    }
    from_1_limit = float(params["max_capacity_from_1"])
    from_2_limit = float(params["max_capacity_from_2"])
    to_8_limit = float(params["max_capacity_to_8"])
    capacity_7_3 = float(params["capacity_7_3"])
    capacity_3_8 = float(params["capacity_3_8"])

    supplied_values = list(source_capacities.values()) + [
        from_1_limit,
        from_2_limit,
        to_8_limit,
        capacity_7_3,
        capacity_3_8,
    ]
    if any(
        not math.isfinite(value) or value < 0
        for value in supplied_values
    ):
        return {"objective": None, "status": "invalid_capacity"}

    explicit_capacities = {
        (0, destination): capacity
        for destination, capacity in source_capacities.items()
    }
    explicit_capacities[7, 3] = capacity_7_3
    explicit_capacities[3, 8] = capacity_3_8

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 8)
    model.transit_stations = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination
        ],
    )
    model.explicit_arcs = pyo.Set(
        dimen=2,
        initialize=list(explicit_capacities),
    )
    model.explicit_capacity = pyo.Param(
        model.explicit_arcs,
        initialize=explicit_capacities,
        within=pyo.NonNegativeReals,
    )
    model.from_1_limit = pyo.Param(
        initialize=from_1_limit,
        within=pyo.NonNegativeReals,
    )
    model.from_2_limit = pyo.Param(
        initialize=from_2_limit,
        within=pyo.NonNegativeReals,
    )
    model.to_8_limit = pyo.Param(
        initialize=to_8_limit,
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def explicit_capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.explicit_capacity[origin, destination]
        )

    model.explicit_capacity_constraints = pyo.Constraint(
        model.explicit_arcs,
        rule=explicit_capacity_rule,
    )

    def from_1_rule(network, destination):
        if destination == 1:
            return pyo.Constraint.Skip
        return network.flow[1, destination] <= network.from_1_limit

    model.from_1_constraints = pyo.Constraint(
        model.stations,
        rule=from_1_rule,
    )

    def from_2_rule(network, destination):
        if destination == 2:
            return pyo.Constraint.Skip
        return network.flow[2, destination] <= network.from_2_limit

    model.from_2_constraints = pyo.Constraint(
        model.stations,
        rule=from_2_rule,
    )

    def to_8_rule(network, origin):
        if origin == 8:
            return pyo.Constraint.Skip
        return network.flow[origin, 8] <= network.to_8_limit

    model.to_8_constraints = pyo.Constraint(
        model.stations,
        rule=to_8_rule,
    )

    def conservation_rule(network, station):
        return (
            sum(
                network.flow[origin, station]
                for origin in network.stations
                if origin != station
            )
            == sum(
                network.flow[station, destination]
                for destination in network.stations
                if destination != station
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in range(1, 9))
            - sum(model.flow[origin, 0] for origin in range(1, 9))
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Unexpected solver errors propagate to the harness.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}