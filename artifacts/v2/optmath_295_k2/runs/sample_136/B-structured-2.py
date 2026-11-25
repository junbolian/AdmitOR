# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j) in N x N : i != j}","I":[1,2,3,4,5]},"params":{"cost[i,j]":"params[f'cost_{i}_{j}']","supply":"params['supply_node_0']","demand":"params['demand_node_6']","balance[k]":"params['balance_nodes_1_to_5'][k-1] if list or tuple; otherwise the scalar params['balance_nodes_1_to_5']","upper_bound":"params['route_usage_upper_bound']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":{"source":"sum(j != 0, x[0,j]) - sum(i != 0, x[i,0]) == supply","destination":"sum(i != 6, x[i,6]) - sum(j != 6, x[6,j]) == demand","intermediate":"sum(i != k, x[i,k]) - sum(j != k, x[k,j]) == balance[k] for k in I","route_limit":"x[i,j] <= upper_bound for (i,j) in A"},"objective":"minimize sum((i,j) in A, cost[i,j] * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
        ordered=True,
    )
    model.intermediate_nodes = pyo.Set(
        initialize=range(1, 6),
        ordered=True,
    )

    balance_input = params["balance_nodes_1_to_5"]
    if isinstance(balance_input, (list, tuple)):
        if len(balance_input) != len(model.intermediate_nodes):
            raise ValueError(
                "balance_nodes_1_to_5 must contain five values, "
                "ordered by nodes 1 through 5."
            )
        balance_values = {
            k: balance_input[k - 1]
            for k in model.intermediate_nodes
        }
    else:
        balance_values = {
            k: balance_input
            for k in model.intermediate_nodes
        }

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_node_0"],
        within=pyo.Reals,
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_node_6"],
        within=pyo.Reals,
    )
    model.intermediate_balance = pyo.Param(
        model.intermediate_nodes,
        initialize=balance_values,
        within=pyo.Reals,
    )
    model.route_upper_bound = pyo.Param(
        initialize=params["route_usage_upper_bound"],
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(
        model.arcs,
        domain=pyo.Binary,
    )

    model.source_flow = pyo.Constraint(
        expr=(
            sum(model.route_used[0, j] for j in model.nodes if j != 0)
            - sum(model.route_used[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )
    model.destination_flow = pyo.Constraint(
        expr=(
            sum(model.route_used[i, 6] for i in model.nodes if i != 6)
            - sum(model.route_used[6, j] for j in model.nodes if j != 6)
            == model.destination_demand
        )
    )

    def intermediate_flow_rule(network, k):
        return (
            sum(
                network.route_used[i, k]
                for i in network.nodes
                if i != k
            )
            - sum(
                network.route_used[k, j]
                for j in network.nodes
                if j != k
            )
            == network.intermediate_balance[k]
        )

    model.intermediate_flow = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_flow_rule,
    )

    def route_limit_rule(network, i, j):
        return network.route_used[i, j] <= network.route_upper_bound

    model.route_limit = pyo.Constraint(
        model.arcs,
        rule=route_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.route_used[i, j]
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