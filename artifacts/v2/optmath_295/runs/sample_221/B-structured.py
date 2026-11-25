# IR: {"sets":{"N":"{0,...,7}","H":"{1,...,6}","A":"{(i,j) in N x N: i != j}"},"params":{"edge_cost[i,j]":"params['edge_cost_<i>_<j>'] for (i,j) in A","supply":"params['net_supply_node_0']","demand":"params['net_demand_node_7']","hub_balance":"params['flow_balance_intermediate']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(j != 0, x[0,j]) - sum(i != 0, x[i,0]) = supply","sum(i != 7, x[i,7]) - sum(j != 7, x[7,j]) = demand","sum(i != h, x[i,h]) - sum(j != h, x[h,j]) = hub_balance for h in H"],"objective":"minimize sum((i,j) in A, edge_cost[i,j] * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(8), ordered=True)
    model.hubs = pyo.Set(initialize=range(1, 7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
        ordered=True,
    )

    model.edge_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"edge_cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["net_supply_node_0"],
        within=pyo.Reals,
    )
    model.sink_demand = pyo.Param(
        initialize=params["net_demand_node_7"],
        within=pyo.Reals,
    )
    model.hub_balance = pyo.Param(
        initialize=params["flow_balance_intermediate"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_flow = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in model.nodes if j != 0)
            - sum(model.x[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )

    model.sink_flow = pyo.Constraint(
        expr=(
            sum(model.x[i, 7] for i in model.nodes if i != 7)
            - sum(model.x[7, j] for j in model.nodes if j != 7)
            == model.sink_demand
        )
    )

    def hub_flow_rule(network, h):
        return (
            sum(network.x[i, h] for i in network.nodes if i != h)
            - sum(network.x[h, j] for j in network.nodes if j != h)
            == network.hub_balance
        )

    model.intermediate_flow = pyo.Constraint(
        model.hubs,
        rule=hub_flow_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.edge_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}