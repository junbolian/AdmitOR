# IR: {"sets":{"N":"0..6","A":"for i=0..6, j=i+1..6: (i,j), (j,i), in that order"},"params":{"node_net_outflow":"real[N], positive=supply, negative=demand","fixed_cost":"real[A], supplied in A order","variable_cost":"real[A], supplied in A order","capacity":"nonnegative real[A], supplied in A order"},"variables":{"flow":"nonnegative continuous[A]","established":"binary[A]"},"constraints":["For each i in N: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) = node_net_outflow[i].","For each (i,j) in A: flow[i,j] <= capacity[i,j] * established[i,j]."],"objective":"Minimize sum(fixed_cost[i,j]*established[i,j] + variable_cost[i,j]*flow[i,j] for (i,j) in A)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [
        arc
        for i in nodes
        for j in range(i + 1, 7)
        for arc in ((i, j), (j, i))
    ]

    net_outflow = params["node_net_outflow"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.node_net_outflow = pyo.Param(
        model.nodes,
        initialize={i: net_outflow[i] for i in nodes},
        within=pyo.Reals,
    )
    model.fixed_cost = pyo.Param(
        model.arcs,
        initialize={arc: fixed_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.arcs,
        initialize={arc: variable_cost[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity[k] for k, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.established = pyo.Var(model.arcs, domain=pyo.Binary)

    def flow_balance_rule(network, i):
        return (
            sum(network.flow[i, j] for j in network.nodes if j != i)
            - sum(network.flow[j, i] for j in network.nodes if j != i)
            == network.node_net_outflow[i]
        )

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )

    def capacity_link_rule(network, i, j):
        return (
            network.flow[i, j]
            <= network.capacity[i, j] * network.established[i, j]
        )

    model.capacity_link = pyo.Constraint(
        model.arcs, rule=capacity_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i, j] * model.established[i, j]
            + model.variable_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}