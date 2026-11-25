# IR: {"sets":{"N":"0..8","A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[3,7],[4,5],[5,6],[5,7],[6,7],[6,8],[7,8]]},"params":{"arc_costs":"unit costs in listed arc order","arc_capacities":"capacity bounds in listed arc order","source_supply":"signed net outflow at node 0","sink_supply":"signed net outflow at node 8","intermediate_node_supply":"seven supplies ordered by nodes 1..7, or one scalar applied to all intermediate nodes"},"variables":{"flow[i,j]":"binary for (i,j) in A"},"constraints":["flow[i,j] <= arc_capacities[position(i,j)] for (i,j) in A","outflow[i] - inflow[i] = supply[i] for i in N; supply[0]=source_supply, supply[8]=sink_supply, supply[1..7]=intermediate_node_supply entries or scalar"],"objective":"minimize sum(arc_costs[position(i,j)] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 4),
        (3, 7),
        (4, 5),
        (5, 6),
        (5, 7),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]
    intermediate_supply = params["intermediate_node_supply"]

    if len(arc_costs) != len(arcs):
        return {"objective": None, "status": "invalid_arc_costs"}

    if len(arc_capacities) != len(arcs):
        return {"objective": None, "status": "invalid_arc_capacities"}

    supplies = {0: source_supply, 8: sink_supply}
    if isinstance(intermediate_supply, (list, tuple)):
        if len(intermediate_supply) != 7:
            return {"objective": None, "status": "invalid_node_supplies"}
        supplies.update(
            {
                node: intermediate_supply[node - 1]
                for node in range(1, 8)
            }
        )
    else:
        supplies.update(
            {node: intermediate_supply for node in range(1, 8)}
        )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.traversal_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_costs[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.capacity_limit = pyo.Param(
        model.arcs,
        initialize={
            arc: arc_capacities[position]
            for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.node_supply = pyo.Param(
        model.nodes,
        initialize=supplies,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(current_model, tail, head):
        return (
            current_model.flow[tail, head]
            <= current_model.capacity_limit[tail, head]
        )

    model.arc_capacity_constraints = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(current_model, node):
        outgoing = sum(
            current_model.flow[tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            current_model.flow[tail, head]
            for tail, head in arcs
            if head == node
        )
        return outgoing - incoming == current_model.node_supply[node]

    model.flow_balance_constraints = pyo.Constraint(
        model.nodes,
        rule=balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.traversal_cost[tail, head] * model.flow[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}