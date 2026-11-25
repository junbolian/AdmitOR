# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j}"},"params":{"arc_cost_i_j":"params['arc_cost_{i}_{j}'] for each (i,j) in A","supply_node_0":"params['supply_node_0']","demand_node_7":"params['demand_node_7']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply_node_0","sum_i x[i,7] - sum_j x[7,j] = demand_node_7","sum_j x[k,j] - sum_i x[i,k] = 0 for k in {1,...,6}"],"objective":"minimize sum_(i,j in A) arc_cost_i_j * x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = tuple(range(8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"arc_cost_{origin}_{destination}"]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_node_0"],
        within=pyo.Reals,
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node_7"],
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(network, node):
        outgoing = sum(
            network.route_used[node, destination]
            for destination in network.nodes
            if destination != node
        )
        incoming = sum(
            network.route_used[origin, node]
            for origin in network.nodes
            if origin != node
        )
        if node == 0:
            return outgoing - incoming == network.source_supply
        if node == 7:
            return incoming - outgoing == network.destination_demand
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[origin, destination]
            * model.route_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}