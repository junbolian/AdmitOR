# IR: {"sets":{"V":"0..8","I":"1..7","S":"{(0,j):j=1..8}","K":"{(1,j):j=2..8} union {(2,1),(2,5)}","U":"{(i,j):i,j in 1..8 and i!=j}","scenarios":["lower","upper"]},"params":{"capacity_0_1":"capacity of (0,1)","capacity_0_2":"capacity of (0,2)","capacity_0_3":"capacity of (0,3)","capacity_0_4":"capacity of (0,4)","capacity_0_5":"capacity of (0,5)","capacity_0_6":"capacity of (0,6)","capacity_0_7":"capacity of (0,7)","capacity_0_8":"capacity of (0,8)","capacity_1_5_high":"capacity of (2,1) and (2,5)","capacity_range_low":"lower bound for generic existing internal arc capacities","capacity_range_high":"upper bound for generic existing internal arc capacities"},"derived_data":{"lower":"source arcs S plus known internal arcs K; generic capacities use capacity_range_low","upper":"source arcs S plus all possible internal arcs U; generic capacities use capacity_range_high","special":"(2,1) and (2,5) always use capacity_1_5_high"},"variables":{"flow[i,j]":"nonnegative continuous for each arc in the scenario"},"constraints":["flow[i,j] <= scenario_capacity[i,j] for every scenario arc","sum incoming flow = sum outgoing flow at each vertex in I"],"objective":"For each scenario, maximize net incoming flow at vertex 8.","reporting":"Return an optimal objective only if both scenario objectives are retrievable and equal; otherwise report objective_unavailable, solver_failure, invalid_capacity_parameters, or ambiguous_network."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Certify the maximum flow from the information actually supplied.

    The statement omits individual internal capacities and some connectivity.
    Replacing that missing information with invented capacities would solve a
    different network. Instead, solve lower and upper bounding networks.

    If their optimal values agree, the missing information cannot affect the
    answer. Otherwise, the supplied parameters do not determine a unique answer,
    and the function returns status='ambiguous_network'.

    Unspecified outgoing arcs from vertex 8 do not affect these bounds: an
    optimal source-to-sink flow can always have zero flow leaving the sink.
    """
    source_capacities = {
        (0, 1): float(params["capacity_0_1"]),
        (0, 2): float(params["capacity_0_2"]),
        (0, 3): float(params["capacity_0_3"]),
        (0, 4): float(params["capacity_0_4"]),
        (0, 5): float(params["capacity_0_5"]),
        (0, 6): float(params["capacity_0_6"]),
        (0, 7): float(params["capacity_0_7"]),
        (0, 8): float(params["capacity_0_8"]),
    }
    special_capacity = float(params["capacity_1_5_high"])
    generic_low = float(params["capacity_range_low"])
    generic_high = float(params["capacity_range_high"])

    numeric_inputs = (
        *source_capacities.values(),
        special_capacity,
        generic_low,
        generic_high,
    )
    if (
        any(not math.isfinite(value) or value < 0 for value in numeric_inputs)
        or generic_low > generic_high
    ):
        return {"objective": None, "status": "invalid_capacity_parameters"}

    special_arcs = {(2, 1), (2, 5)}
    known_internal_arcs = {
        (1, destination) for destination in range(2, 9)
    } | special_arcs
    possible_internal_arcs = {
        (origin, destination)
        for origin in range(1, 9)
        for destination in range(1, 9)
        if origin != destination
    }

    def solve_scenario(internal_arcs, generic_capacity):
        capacities = dict(source_capacities)
        for origin, destination in sorted(internal_arcs):
            capacities[origin, destination] = (
                special_capacity
                if (origin, destination) in special_arcs
                else generic_capacity
            )

        incoming = {
            vertex: [
                arc for arc in capacities if arc[1] == vertex
            ]
            for vertex in range(9)
        }
        outgoing = {
            vertex: [
                arc for arc in capacities if arc[0] == vertex
            ]
            for vertex in range(9)
        }

        model = pyo.ConcreteModel()
        model.vertices = pyo.RangeSet(0, 8)
        model.intermediate_vertices = pyo.RangeSet(1, 7)
        model.arcs = pyo.Set(dimen=2, initialize=sorted(capacities))
        model.arc_capacity = pyo.Param(
            model.arcs,
            initialize=capacities,
            within=pyo.NonNegativeReals,
        )
        model.flow = pyo.Var(
            model.arcs,
            domain=pyo.NonNegativeReals,
        )

        def capacity_rule(network, origin, destination):
            return (
                network.flow[origin, destination]
                <= network.arc_capacity[origin, destination]
            )

        model.capacity_limits = pyo.Constraint(
            model.arcs,
            rule=capacity_rule,
        )

        def conservation_rule(network, vertex):
            return (
                pyo.quicksum(
                    network.flow[arc] for arc in incoming[vertex]
                )
                == pyo.quicksum(
                    network.flow[arc] for arc in outgoing[vertex]
                )
            )

        model.flow_conservation = pyo.Constraint(
            model.intermediate_vertices,
            rule=conservation_rule,
        )
        model.total_flow = pyo.Objective(
            expr=(
                pyo.quicksum(model.flow[arc] for arc in incoming[8])
                - pyo.quicksum(model.flow[arc] for arc in outgoing[8])
            ),
            sense=pyo.maximize,
        )

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            if "feasible solution was not found" in str(exc).lower():
                return {"objective": None, "status": "solver_failure"}
            raise

        try:
            obj_val = float(pyo.value(model.total_flow))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        return {"objective": obj_val, "status": "optimal"}

    lower_result = solve_scenario(known_internal_arcs, generic_low)
    if lower_result["objective"] is None:
        return lower_result

    upper_result = solve_scenario(possible_internal_arcs, generic_high)
    if upper_result["objective"] is None:
        return upper_result

    # This comparison checks whether the problem data determine one answer;
    # it does not inspect or compare solver termination conditions.
    if lower_result["objective"] != upper_result["objective"]:
        return {"objective": None, "status": "ambiguous_network"}

    return {
        "objective": float(lower_result["objective"]),
        "status": "optimal",
    }