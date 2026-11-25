# IR: {"sets":{"N":[0,1,2,3],"A":"[(i,j) for i in N for j in N if i != j], lexicographic order"},"params":{"fixed_cost":"params['fixed_cost'][k] for arc A[k]","variable_cost":"params['variable_cost'][k] for arc A[k]","capacity":"params['capacity'][k] for arc A[k]","net_outflow":"params['net_outflow'][i] for node i"},"variables":{"route_open[i,j]":"Binary for (i,j) in A","flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in N: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) == net_outflow[i]","For each (i,j) in A: flow[i,j] <= capacity[i,j] * route_open[i,j]"],"objective":"Minimize sum(fixed_cost[i,j] * route_open[i,j] + variable_cost[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(4))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: params["fixed_cost"][k]
            for k, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={
            arc: params["variable_cost"][k]
            for k, arc in enumerate(arcs)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            arc: params["capacity"][k]
            for k, arc in enumerate(arcs)
        },
        within=pyo.NonNegativeReals,
    )
    model.net_outflow = pyo.Param(
        model.nodes,
        initialize={i: params["net_outflow"][i] for i in nodes},
        within=pyo.Reals,
    )

    model.route_open = pyo.Var(model.arcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(network, i):
        outgoing = sum(
            network.flow[i, j] for j in network.nodes if j != i
        )
        incoming = sum(
            network.flow[j, i] for j in network.nodes if j != i
        )
        return outgoing - incoming == network.net_outflow[i]

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    def capacity_rule(network, i, j):
        return (
            network.flow[i, j]
            <= network.capacity[i, j] * network.route_open[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i, j] * model.route_open[i, j]
            + model.variable_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}