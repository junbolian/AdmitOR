# IR: {"sets":{"nodes":[0,1,2,3,4,5,6],"arcs":[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[1,2],[1,3]]},"params":{"node_0_supply":"real","node_6_demand":"real","cost_0_1":"real","cost_0_2":"real","cost_0_3":"real","cost_0_4":"real","cost_0_5":"real","cost_0_6":"real","cost_1_2":"real","cost_1_3":"real"},"variables":{"route_used[i,j]":"binary for (i,j) in arcs"},"constraints":["sum(outgoing route_used)-sum(incoming route_used)=node_0_supply at node 0","sum(incoming route_used)-sum(outgoing route_used)=node_6_demand at node 6","sum(outgoing route_used)-sum(incoming route_used)=0 at nodes 1 through 5"],"objective":"minimize sum(cost_i_j * route_used[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Only routes with explicitly supplied cost parameters are modeled.
    # The narrative mentions additional routes but supplies no full cost list.
    nodes = tuple(range(7))
    arcs = (
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (0, 5),
        (0, 6),
        (1, 2),
        (1, 3),
    )

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

    model.source_supply = pyo.Param(
        initialize=params["node_0_supply"], within=pyo.Reals
    )
    model.sink_demand = pyo.Param(
        initialize=params["node_6_demand"], within=pyo.Reals
    )
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (0, 1): params["cost_0_1"],
            (0, 2): params["cost_0_2"],
            (0, 3): params["cost_0_3"],
            (0, 4): params["cost_0_4"],
            (0, 5): params["cost_0_5"],
            (0, 6): params["cost_0_6"],
            (1, 2): params["cost_1_2"],
            (1, 3): params["cost_1_3"],
        },
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(current_model, node):
        outflow = sum(
            current_model.route_used[arc] for arc in outgoing[node]
        )
        inflow = sum(
            current_model.route_used[arc] for arc in incoming[node]
        )
        if node == 0:
            return outflow - inflow == current_model.source_supply
        if node == 6:
            return inflow - outflow == current_model.sink_demand
        return outflow - inflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[arc] * model.route_used[arc]
            for arc in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}