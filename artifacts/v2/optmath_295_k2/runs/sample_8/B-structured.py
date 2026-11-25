# IR: {"sets":{"N":"{0,...,7}","A":"[(i,j) for i in N for j in N if i != j]","I":"{1,...,6}"},"params":{"cost":"real vector indexed in A order","net_outflow_node_0":"real","net_inflow_node_7":"real"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[0,j] for j != 0)-sum(x[i,0] for i != 0)=net_outflow_node_0","sum(x[i,7] for i != 7)-sum(x[7,j] for j != 7)=net_inflow_node_7","sum(x[i,k] for i != k)-sum(x[k,j] for j != k)=0 for k in I"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
    )

    costs = list(params["cost"])
    required_outflow = params["net_outflow_node_0"]
    required_inflow = params["net_inflow_node_7"]

    if len(costs) != len(arcs):
        raise ValueError("params['cost'] must contain one value per directed arc.")

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_nodes = pyo.Set(initialize=range(1, 7), ordered=True)

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: costs[position] for position, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.required_outflow = pyo.Param(
        initialize=required_outflow, within=pyo.Reals
    )
    model.required_inflow = pyo.Param(
        initialize=required_inflow, within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, destination] for destination in nodes if destination != 0)
            - sum(model.x[origin, 0] for origin in nodes if origin != 0)
            == model.required_outflow
        )
    )

    model.destination_balance = pyo.Constraint(
        expr=(
            sum(model.x[origin, 7] for origin in nodes if origin != 7)
            - sum(model.x[7, destination] for destination in nodes if destination != 7)
            == model.required_inflow
        )
    )

    def intermediate_balance_rule(network, hub):
        return (
            sum(network.x[origin, hub] for origin in nodes if origin != hub)
            - sum(
                network.x[hub, destination]
                for destination in nodes
                if destination != hub
            )
            == 0
        )

    model.intermediate_balance = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}