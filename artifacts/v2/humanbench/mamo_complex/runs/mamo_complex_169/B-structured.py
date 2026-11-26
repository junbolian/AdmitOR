# IR: {"sets":{"N":[0,1,2,3,4,5],"A":"[(i,j) for i in N for j in N if i != j]","T":[1,2,3,4]},"params":{"capacity[i,j]":"nonnegative capacity read from params['capacity']; flat 30-entry data follow A order; alternatively accept a tuple-keyed mapping or a 6-by-6 nested container"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for j in N if j != i) = sum(flow[j,i] for j in N if j != i) for every i in T"],"objective":"maximize sum(flow[0,j] for j in N if j != 0) - sum(flow[j,0] for j in N if j != 0)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Compute maximum net flow from station 0 to station 5.

    Supported params["capacity"] formats:
      * A flat sequence of 30 capacities, ordered by source station,
        then destination station, skipping self-arcs.
      * A mapping keyed by (source, destination) tuples.
      * A 6-by-6 nested mapping or sequence; diagonals are ignored.
      * A mapping keyed by integers 0 through 29 in flat-sequence order.

    All capacities, including arcs entering the source and leaving the
    sink, come exclusively from params["capacity"].
    """
    nodes = list(range(6))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    capacity_data = params["capacity"]

    if isinstance(capacity_data, Mapping) and all(
        arc in capacity_data for arc in arcs
    ):
        capacities = {arc: capacity_data[arc] for arc in arcs}
    elif len(capacity_data) == len(arcs):
        capacities = {
            arc: capacity_data[position]
            for position, arc in enumerate(arcs)
        }
    else:
        capacities = {
            (i, j): capacity_data[i][j]
            for i, j in arcs
        }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_nodes = pyo.Set(initialize=range(1, 5), ordered=True)

    model.cable_capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.cable_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, i):
        return (
            sum(network.flow[i, j] for j in network.nodes if j != i)
            == sum(network.flow[j, i] for j in network.nodes if j != i)
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[j, 0] for j in model.nodes if j != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}