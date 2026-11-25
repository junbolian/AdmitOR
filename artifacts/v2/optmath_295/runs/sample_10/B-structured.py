# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j) in N x N: i != j}","I":[1,2,3,4,5]},"params":{"supply_node_0":"required net outflow at node 0","demand_node_6":"required net inflow at node 6","cost_i_j":"params[cost_i_j] for every (i,j) in A"},"variables":{"x[i,j]":{"index":"A","type":"binary"}},"constraints":["sum(x[0,j] for j != 0) - sum(x[i,0] for i != 0) = supply_node_0","sum(x[i,6] for i != 6) - sum(x[6,j] for j != 6) = demand_node_6","sum(x[k,j] for j != k) - sum(x[i,k] for i != k) = 0 for k in I"],"objective":{"sense":"minimize","expression":"sum(cost_i_j * x[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(7)
            for destination in range(7)
            if origin != destination
        ],
        ordered=True,
    )
    model.intermediate_nodes = pyo.Set(initialize=range(1, 6), ordered=True)

    model.source_supply = pyo.Param(
        initialize=params["supply_node_0"],
        within=pyo.Reals,
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node_6"],
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[0, destination] for destination in model.nodes if destination != 0)
            - sum(model.route_used[origin, 0] for origin in model.nodes if origin != 0)
            == model.source_supply
        )
    )

    model.destination_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[origin, 6] for origin in model.nodes if origin != 6)
            - sum(model.route_used[6, destination] for destination in model.nodes if destination != 6)
            == model.destination_demand
        )
    )

    def intermediate_balance_rule(mdl, hub):
        return (
            sum(
                mdl.route_used[hub, destination]
                for destination in mdl.nodes
                if destination != hub
            )
            - sum(
                mdl.route_used[origin, hub]
                for origin in mdl.nodes
                if origin != hub
            )
            == 0
        )

    model.intermediate_balance = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination]
            * model.route_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}