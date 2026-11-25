# IR: {"sets":{"N":"{0,...,6}","A":"[(i,j),(j,i) for 0<=i<j<=6], in that order"},"params":{"supply_node0":"params['supply_node0']","supply_node1":"params['supply_node1']","demand_node5":"params['demand_node5']","demand_node6":"params['demand_node6']","fixed_cost_matrix":"params['fixed_cost_matrix']; arc costs F","variable_cost_matrix":"params['variable_cost_matrix']; arc costs C","capacity_matrix":"params['capacity_matrix']; nonnegative arc capacities U","matrix_formats":"42 entries, 21 rows of 2 entries in arc order, or 7x7 indexed by node","b":"{0:supply_node0,1:supply_node1,2:0,3:0,4:0,5:-demand_node5,6:-demand_node6}"},"variables":{"flow[i,j]":"nonnegative real for (i,j) in A","opened[i,j]":"binary for (i,j) in A"},"constraints":["For each n in N: sum(flow[n,j]) - sum(flow[i,n]) = b[n].","For each (i,j) in A: flow[i,j] <= U[i,j]*opened[i,j]."],"objective":"minimize sum(F[i,j]*opened[i,j] + C[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _arc_values(data, arcs, parameter_name):
    """Normalize supported input layouts to an arc-indexed dictionary."""
    rows = list(data)

    if len(rows) == 42:
        values = rows
    elif len(rows) == 21:
        pairs = [list(row) for row in rows]
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError(
                f"{parameter_name}: each of the 21 rows must have 2 entries."
            )
        values = [value for pair in pairs for value in pair]
    elif len(rows) == 7:
        square = [list(row) for row in rows]
        if any(len(row) != 7 for row in square):
            raise ValueError(
                f"{parameter_name}: a node-indexed matrix must be 7 by 7."
            )
        values = [square[source][target] for source, target in arcs]
    else:
        raise ValueError(
            f"{parameter_name}: expected 42 entries, 21 by 2, or 7 by 7."
        )

    return {arc: float(value) for arc, value in zip(arcs, values)}


def solve(params):
    nodes = tuple(range(7))
    arcs = tuple(
        arc
        for source in nodes
        for target in nodes
        if source < target
        for arc in ((source, target), (target, source))
    )

    net_outflow = {
        0: float(params["supply_node0"]),
        1: float(params["supply_node1"]),
        2: 0,
        3: 0,
        4: 0,
        5: -float(params["demand_node5"]),
        6: -float(params["demand_node6"]),
    }

    fixed_costs = _arc_values(
        params["fixed_cost_matrix"], arcs, "fixed_cost_matrix"
    )
    variable_costs = _arc_values(
        params["variable_cost_matrix"], arcs, "variable_cost_matrix"
    )
    capacities = _arc_values(
        params["capacity_matrix"], arcs, "capacity_matrix"
    )

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=arcs, within=model.nodes * model.nodes, ordered=True
    )

    model.net_outflow = pyo.Param(
        model.nodes, initialize=net_outflow, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.arcs, initialize=fixed_costs, within=pyo.Reals
    )
    model.variable_cost = pyo.Param(
        model.arcs, initialize=variable_costs, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.opened = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(network, node):
        outgoing = sum(
            network.flow[node, target]
            for target in network.nodes
            if target != node
        )
        incoming = sum(
            network.flow[source, node]
            for source in network.nodes
            if source != node
        )
        return outgoing - incoming == network.net_outflow[node]

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    def capacity_rule(network, source, target):
        return (
            network.flow[source, target]
            <= network.capacity[source, target] * network.opened[source, target]
        )

    model.capacity_link = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[source, target] * model.opened[source, target]
            + model.variable_cost[source, target] * model.flow[source, target]
            for source, target in model.arcs
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