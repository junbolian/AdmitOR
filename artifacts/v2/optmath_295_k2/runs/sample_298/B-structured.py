# IR: {"sets":{"N":"0..9","A":"{(i,j): i in {0,1}, j in N, i!=j}; only arcs with provided costs"},"params":{"supply_node0":"params['supply_node0']","demand_node9":"params['demand_node9']","intermediate_net_flow":"params['intermediate_net_flow']","cost[i,j]":"params['cost_node{i}_to_node{j}'], (i,j) in A"},"variables":{"x[i,j]":"binary, (i,j) in A"},"constraints":["outflow(0)-inflow(0)=supply_node0","inflow(9)-outflow(9)=demand_node9","outflow(k)-inflow(k)=intermediate_net_flow, k=1..8"],"objective":"minimize sum_{(i,j) in A} cost[i,j]*x[i,j]"}
#
# Costs for arcs originating at nodes 2 through 9 are not provided.
# Those arcs are excluded rather than assigned invented costs.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(10))
    arcs = tuple(
        (origin, destination)
        for origin in (0, 1)
        for destination in nodes
        if origin != destination
    )

    costs = {
        (origin, destination): params[
            f"cost_node{origin}_to_node{destination}"
        ]
        for origin, destination in arcs
    }

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply_node0 = pyo.Param(initialize=params["supply_node0"])
    model.demand_node9 = pyo.Param(initialize=params["demand_node9"])
    model.intermediate_net_flow = pyo.Param(
        initialize=params["intermediate_net_flow"]
    )
    model.arc_cost = pyo.Param(model.arcs, initialize=costs)
    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(instance, node):
        net_outflow = (
            pyo.quicksum(instance.route_used[arc] for arc in outgoing[node])
            - pyo.quicksum(instance.route_used[arc] for arc in incoming[node])
        )

        # Equality tuples avoid evaluation to a native Python Boolean,
        # including when a balance expression contains no variables.
        if node == 0:
            return (net_outflow, instance.supply_node0)
        if node == 9:
            return (-net_outflow, instance.demand_node9)
        return (net_outflow, instance.intermediate_net_flow)

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.arc_cost[origin, destination]
            * model.route_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}