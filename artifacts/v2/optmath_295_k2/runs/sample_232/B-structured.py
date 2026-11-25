# IR: {"sets":{"N":"range(params['num_nodes'])","A":"{(i,j) in N x N: i != j}"},"params":{"fixed_cost[i,j]":"params['fixed_cost_{i}_{j}'] for (i,j) in A","variable_cost[i,j]":"params['variable_cost_{i}_{j}'] for (i,j) in A","capacity[i,j]":"params['capacity_{i}_{j}'] for (i,j) in A","net_outflow[i]":"params['net_outflow_node{i}'] for i in N","num_nodes":"params['num_nodes'] (frozen at four)"},"variables":{"route_open[i,j]":"Binary for (i,j) in A","flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["For each i in N: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) = net_outflow[i]","For each (i,j) in A: flow[i,j] <= capacity[i,j] * route_open[i,j]"],"objective":"Minimize sum(fixed_cost[i,j]*route_open[i,j] + variable_cost[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    nodes = list(range(num_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    fixed_cost = {
        (i, j): params[f"fixed_cost_{i}_{j}"] for i, j in arcs
    }
    variable_cost = {
        (i, j): params[f"variable_cost_{i}_{j}"] for i, j in arcs
    }
    capacity = {
        (i, j): params[f"capacity_{i}_{j}"] for i, j in arcs
    }
    net_outflow = {
        i: params[f"net_outflow_node{i}"] for i in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.fixed_cost = pyo.Param(
        model.arcs, initialize=fixed_cost, within=pyo.Reals
    )
    model.variable_cost = pyo.Param(
        model.arcs, initialize=variable_cost, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.net_outflow = pyo.Param(
        model.nodes, initialize=net_outflow, within=pyo.Reals
    )

    model.route_open = pyo.Var(model.arcs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def flow_balance_rule(network, i):
        return (
            sum(network.flow[i, j] for j in network.nodes if j != i)
            - sum(network.flow[j, i] for j in network.nodes if j != i)
            == network.net_outflow[i]
        )

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )

    def route_capacity_rule(network, i, j):
        return (
            network.flow[i, j]
            <= network.capacity[i, j] * network.route_open[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs, rule=route_capacity_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}