# IR: {"sets":{"N":"range(num_nodes), frozen at 6","P":"range(num_pipes), frozen at 17","arcs":[[0,1],[0,2],[0,5],[1,0],[1,2],[2,0],[2,1],[2,3],[3,2],[3,4],[4,1],[4,2],[4,3],[4,5],[5,0],[5,3],[5,4]]},"params":{"unit_cost":"P-indexed array from params","min_flow":"P-indexed array from params","capacity":"P-indexed array from params","node_x":"N-indexed geometry array from params; unused in LP coefficients","node_y":"N-indexed geometry array from params; unused in LP coefficients","num_nodes":"frozen node count from params","num_pipes":"frozen pipe count from params"},"variables":{"flow[p]":"nonnegative continuous, p in P"},"constraints":["flow[p] >= min_flow[p], for each p in P","flow[p] <= capacity[p], for each p in P","sum(flow[p] for arcs entering n) == sum(flow[p] for arcs leaving n), for each n in N"],"objective":"minimize sum(unit_cost[p] * flow[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    )

    num_nodes = params["num_nodes"]
    num_pipes = params["num_pipes"]
    unit_cost = params["unit_cost"]
    min_flow = params["min_flow"]
    capacity = params["capacity"]
    node_x = params["node_x"]
    node_y = params["node_y"]

    if num_nodes != 6 or num_pipes != len(arcs):
        raise ValueError("The network requires 6 nodes and 17 pipes.")

    for parameter_name, values, expected_length in (
        ("unit_cost", unit_cost, num_pipes),
        ("min_flow", min_flow, num_pipes),
        ("capacity", capacity, num_pipes),
        ("node_x", node_x, num_nodes),
        ("node_y", node_y, num_nodes),
    ):
        if len(values) != expected_length:
            raise ValueError(
                f"{parameter_name} must contain {expected_length} entries."
            )

    incoming = {
        node: tuple(
            pipe for pipe, (_, head) in enumerate(arcs) if head == node
        )
        for node in range(num_nodes)
    }
    outgoing = {
        node: tuple(
            pipe for pipe, (tail, _) in enumerate(arcs) if tail == node
        )
        for node in range(num_nodes)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.pipes = pyo.Set(initialize=range(num_pipes), ordered=True)

    model.unit_cost = pyo.Param(
        model.pipes,
        initialize={pipe: unit_cost[pipe] for pipe in range(num_pipes)},
        within=pyo.Reals,
    )
    model.min_flow = pyo.Param(
        model.pipes,
        initialize={pipe: min_flow[pipe] for pipe in range(num_pipes)},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.pipes,
        initialize={pipe: capacity[pipe] for pipe in range(num_pipes)},
        within=pyo.NonNegativeReals,
    )
    model.node_x = pyo.Param(
        model.nodes,
        initialize={node: node_x[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )
    model.node_y = pyo.Param(
        model.nodes,
        initialize={node: node_y[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.pipes, domain=pyo.NonNegativeReals)

    def minimum_flow_rule(network, pipe):
        return network.flow[pipe] >= network.min_flow[pipe]

    def capacity_rule(network, pipe):
        return network.flow[pipe] <= network.capacity[pipe]

    def flow_balance_rule(network, node):
        return (
            sum(network.flow[pipe] for pipe in incoming[node])
            == sum(network.flow[pipe] for pipe in outgoing[node])
        )

    model.minimum_flow_constraints = pyo.Constraint(
        model.pipes, rule=minimum_flow_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.pipes, rule=capacity_rule
    )
    model.flow_balance_constraints = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[pipe] * model.flow[pipe]
            for pipe in model.pipes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}