# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"I":[1,2,3,4,5,6,7,8],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],[0,9],[1,0],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[1,8],[1,9]]},"params":["supply_node0","demand_node9","cost_0_1","cost_0_2","cost_0_3","cost_0_4","cost_0_5","cost_0_6","cost_0_7","cost_0_8","cost_0_9","cost_1_0","cost_1_2","cost_1_3","cost_1_4","cost_1_5","cost_1_6","cost_1_7","cost_1_8","cost_1_9"],"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(x[0,j] for (0,j) in A) = supply_node0","sum(x[i,9] for (i,9) in A) = demand_node9","sum(x[i,k] for (i,k) in A) = sum(x[k,j] for (k,j) in A), for k in I"],"objective":"minimize sum(cost_i_j * x[i,j] for (i,j) in A)","scope":"Only arcs with costs listed in PARAMS are available; costs for other arcs are unspecified."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(10))
    intermediate_nodes = tuple(range(1, 9))

    # The supplied parameter schema provides costs only for these arcs.
    arcs = tuple(
        (origin, destination)
        for origin in (0, 1)
        for destination in nodes
        if origin != destination
    )

    supply = params["supply_node0"]
    demand = params["demand_node9"]
    arc_costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }

    incoming_arcs = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing_arcs = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=intermediate_nodes, ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply_amount = pyo.Param(initialize=supply, within=pyo.Reals)
    model.demand_amount = pyo.Param(initialize=demand, within=pyo.Reals)
    model.transport_cost = pyo.Param(
        model.arcs, initialize=arc_costs, within=pyo.Reals
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.supply_requirement = pyo.Constraint(
        expr=sum(
            model.route_used[origin, destination]
            for origin, destination in outgoing_arcs[0]
        )
        == model.supply_amount
    )

    model.demand_requirement = pyo.Constraint(
        expr=sum(
            model.route_used[origin, destination]
            for origin, destination in incoming_arcs[9]
        )
        == model.demand_amount
    )

    def conservation_rule(instance, node):
        inflow = sum(
            instance.route_used[origin, destination]
            for origin, destination in incoming_arcs[node]
        )
        outflow = sum(
            instance.route_used[origin, destination]
            for origin, destination in outgoing_arcs[node]
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.route_used[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi HiGHS raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}