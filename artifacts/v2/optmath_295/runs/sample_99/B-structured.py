# IR: {"sets":{"N":"range(num_nodes)","A":"[(i,j) for i in N for j in N if i!=j], lexicographic order"},"params":{"num_nodes":"params['num_nodes']; frozen node count","net_demand":"params['net_demand'][i]","fixed_cost":"params['fixed_cost'][k] for arc A[k]","variable_cost":"params['variable_cost'][k] for arc A[k]","capacity":"params['capacity'][k] for arc A[k]"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in A","opened[i,j]":"binary, (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j]*opened[i,j] for (i,j) in A","sum(flow[j,i] for j!=i)-sum(flow[i,j] for j!=i) == net_demand[i] for i in N"],"objective":"minimize sum(fixed_cost[i,j]*opened[i,j]+variable_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    net_demand = params["net_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    nodes = list(range(num_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_demand = pyo.Param(
        model.nodes,
        initialize={i: net_demand[i] for i in nodes},
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
    model.opened = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(network, i, j):
        return (
            network.flow[i, j]
            <= network.capacity[i, j] * network.opened[i, j]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, i):
        incoming = pyo.quicksum(
            network.flow[j, i] for j in network.nodes if j != i
        )
        outgoing = pyo.quicksum(
            network.flow[i, j] for j in network.nodes if j != i
        )
        return incoming - outgoing == network.net_demand[i]

    model.node_balances = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.fixed_cost[i, j] * model.opened[i, j]
            + model.variable_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
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