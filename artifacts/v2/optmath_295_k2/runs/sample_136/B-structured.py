# IR: {"sets":{"N":"{0,...,6}","A":"{(i,j) in N x N: i != j}","I":"{1,...,5}"},"params":{"cost[i,j]":"params['cost_{i}_{j}'] for (i,j) in A","supply":"params['supply_node_0']","demand":"params['demand_node_6']","balance[k]":"params['balance_nodes_1_to_5'][k-1] if a list or tuple; otherwise the supplied scalar, for k in I","capacity":"params['route_usage_upper_bound']"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum(j != 0, x[0,j]) - sum(i != 0, x[i,0]) = supply","sum(i != 6, x[i,6]) - sum(j != 6, x[6,j]) = demand","for k in I: sum(i != k, x[i,k]) - sum(j != k, x[k,j]) = balance[k]","for (i,j) in A: x[i,j] <= capacity"],"objective":"minimize sum((i,j) in A, cost[i,j] * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=range(1, 6), ordered=True
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (source, target)
            for source in range(7)
            for target in range(7)
            if source != target
        ],
        ordered=True,
    )

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (source, target): params[f"cost_{source}_{target}"]
            for source, target in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_node_0"], within=pyo.Reals
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node_6"], within=pyo.Reals
    )

    balance_values = params["balance_nodes_1_to_5"]
    if isinstance(balance_values, (list, tuple)):
        if len(balance_values) != len(model.intermediate_nodes):
            return {"objective": None, "status": "invalid_balance_length"}
        balance_by_node = {
            node: balance_values[node - 1]
            for node in model.intermediate_nodes
        }
    else:
        balance_by_node = {
            node: balance_values for node in model.intermediate_nodes
        }

    model.intermediate_requirement = pyo.Param(
        model.intermediate_nodes,
        initialize=balance_by_node,
        within=pyo.Reals,
    )
    model.route_capacity_limit = pyo.Param(
        initialize=params["route_usage_upper_bound"], within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, target] for target in model.nodes if target != 0)
            - sum(model.x[source, 0] for source in model.nodes if source != 0)
            == model.source_supply
        )
    )

    model.destination_balance = pyo.Constraint(
        expr=(
            sum(model.x[source, 6] for source in model.nodes if source != 6)
            - sum(model.x[6, target] for target in model.nodes if target != 6)
            == model.destination_demand
        )
    )

    def intermediate_balance_rule(mdl, node):
        return (
            sum(mdl.x[source, node] for source in mdl.nodes if source != node)
            - sum(mdl.x[node, target] for target in mdl.nodes if target != node)
            == mdl.intermediate_requirement[node]
        )

    model.intermediate_balance = pyo.Constraint(
        model.intermediate_nodes, rule=intermediate_balance_rule
    )

    model.route_capacity = pyo.Constraint(
        model.arcs,
        rule=lambda mdl, source, target: (
            mdl.x[source, target] <= mdl.route_capacity_limit
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[source, target] * model.x[source, target]
            for source, target in model.arcs
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