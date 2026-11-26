# IR: {
#   "sets": {"N": [0,1,2,3,4,5,6,7], "A": "[(i,j) for i in N for j in N if i != j]", "T": [1,2,3,4,5,6]},
#   "params": {"capacity_0_1": "scalar", "capacity_0_2": "scalar", "capacity_0_3": "scalar", "capacity_0_4": "scalar", "capacity_0_5": "scalar", "capacity_0_6": "scalar", "capacity_0_7": "scalar", "capacities_from_1": "length-7 array", "capacities_from_2": "length-7 array", "capacities_from_3": "length-7 array", "capacities_from_4": "length-7 array", "capacities_from_5": "length-7 array", "capacities_from_6": "length-7 array", "capacities_from_7": "length-7 array"},
#   "derived_params": {"capacity[i,j]": "row i from params, ordered by ascending destination j excluding i"},
#   "decision_variables": {"flow[i,j]": "nonnegative continuous for (i,j) in A"},
#   "constraints": [
#     "flow[i,j] <= capacity[i,j] for every (i,j) in A",
#     "sum(flow[i,j] for j in N if j != i) == sum(flow[j,i] for j in N if j != i) for every i in T"
#   ],
#   "objective": "maximize sum(flow[0,j] for j in N if j != 0) - sum(flow[j,0] for j in N if j != 0)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = [(src, dst) for src in nodes for dst in nodes if src != dst]

    capacity_rows = {
        0: [
            params["capacity_0_1"],
            params["capacity_0_2"],
            params["capacity_0_3"],
            params["capacity_0_4"],
            params["capacity_0_5"],
            params["capacity_0_6"],
            params["capacity_0_7"],
        ],
        1: params["capacities_from_1"],
        2: params["capacities_from_2"],
        3: params["capacities_from_3"],
        4: params["capacities_from_4"],
        5: params["capacities_from_5"],
        6: params["capacities_from_6"],
        7: params["capacities_from_7"],
    }

    capacities = {}
    for src in nodes:
        destinations = [dst for dst in nodes if dst != src]
        if len(capacity_rows[src]) != len(destinations):
            return {"objective": None, "status": "invalid_capacity_length"}
        for position, dst in enumerate(destinations):
            capacities[src, dst] = capacity_rows[src][position]

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_set = pyo.Set(initialize=range(1, 7), ordered=True)

    model.capacity = pyo.Param(
        model.arc_set,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def capacity_rule(network, src, dst):
        return network.flow[src, dst] <= network.capacity[src, dst]

    model.tunnel_limits = pyo.Constraint(
        model.arc_set,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        outgoing = sum(
            network.flow[node, dst]
            for dst in network.node_set
            if dst != node
        )
        incoming = sum(
            network.flow[src, node]
            for src in network.node_set
            if src != node
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.transit_set,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, dst] for dst in nodes if dst != 0)
            - sum(model.flow[src, 0] for src in nodes if src != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}