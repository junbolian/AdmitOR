# IR: {"sets":{"N":"0..num_nodes-1 (frozen at 6)","A":"[(0,1),(0,2),(0,5),(1,0),(1,2),(2,0),(2,1),(2,3),(3,2),(3,4),(4,1),(4,2),(4,3),(4,5),(5,0),(5,3),(5,4)] (num_pipes frozen at 17)"},"params":{"unit_cost":"real[A], supplied in arc order","min_flow":"real[A], supplied in arc order","capacity":"real[A], supplied in arc order","node_x":"real[N], geometry only","node_y":"real[N], geometry only","num_nodes":"frozen node count","num_pipes":"frozen arc count"},"variables":{"flow[a]":"continuous nonnegative, a in A"},"constraints":["flow[a] >= min_flow[a], all a in A","flow[a] <= capacity[a], all a in A","sum(flow[i,j] for (i,j) in A if j=n) = sum(flow[i,j] for (i,j) in A if i=n), all n in N"],"objective":"minimize sum(unit_cost[a] * flow[a] for a in A)"}

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
        raise ValueError("The network is frozen at six nodes and seventeen pipes.")

    for label, values in (
        ("unit_cost", unit_cost),
        ("min_flow", min_flow),
        ("capacity", capacity),
    ):
        if len(values) != num_pipes:
            raise ValueError(f"{label} must contain {num_pipes} entries.")

    for label, values in (("node_x", node_x), ("node_y", node_y)):
        if len(values) != num_nodes:
            raise ValueError(f"{label} must contain {num_nodes} entries.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(int(num_nodes)), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={arc: unit_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.min_flow = pyo.Param(
        model.arcs,
        initialize={arc: min_flow[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.node_x = pyo.Param(
        model.nodes,
        initialize={node: node_x[node] for node in range(int(num_nodes))},
        within=pyo.Reals,
    )
    model.node_y = pyo.Param(
        model.nodes,
        initialize={node: node_y[node] for node in range(int(num_nodes))},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def minimum_flow_rule(network, source, destination):
        return (
            network.flow[source, destination]
            >= network.min_flow[source, destination]
        )

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
        )

    def balance_rule(network, node):
        inflow = sum(
            network.flow[source, destination]
            for source, destination in network.arcs
            if destination == node
        )
        outflow = sum(
            network.flow[source, destination]
            for source, destination in network.arcs
            if source == node
        )
        return inflow == outflow

    model.minimum_flow_constraints = pyo.Constraint(
        model.arcs, rule=minimum_flow_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )
    model.balance_constraints = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}