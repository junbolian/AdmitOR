# IR: {"sets":{"N":"0..7","A":"[(i,j) for i in N for j in N if i!=j]","T":"1..6"},"params":{"edge_costs":"real[56], ordered lexicographically by (i,j) in A","node0_outflow_inflow_excess":"real","node7_inflow_outflow_excess":"real"},"variables":{"x[i,j]":"binary, (i,j) in A"},"constraints":["sum(x[0,j] for j!=0)-sum(x[i,0] for i!=0)=node0_outflow_inflow_excess","sum(x[i,7] for i!=7)-sum(x[7,j] for j!=7)=node7_inflow_outflow_excess","for k in T: sum(x[i,k] for i!=k)=sum(x[k,j] for j!=k)"],"objective":"minimize sum(edge_costs[position(i,j)]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    edge_costs = params["edge_costs"]
    source_excess = params["node0_outflow_inflow_excess"]
    sink_excess = params["node7_inflow_outflow_excess"]

    if len(edge_costs) != len(edges):
        return {"objective": None, "status": "invalid_edge_costs_length"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.edges = pyo.Set(initialize=edges, dimen=2, ordered=True)
    model.transit_nodes = pyo.Set(initialize=range(1, 7), ordered=True)

    model.route_cost = pyo.Param(
        model.edges,
        initialize={
            edge: edge_costs[position]
            for position, edge in enumerate(edges)
        },
        within=pyo.Reals,
    )
    model.source_excess = pyo.Param(
        initialize=source_excess, within=pyo.Reals
    )
    model.sink_excess = pyo.Param(
        initialize=sink_excess, within=pyo.Reals
    )

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in nodes if j != 0)
            - sum(model.x[i, 0] for i in nodes if i != 0)
            == model.source_excess
        )
    )

    model.sink_balance = pyo.Constraint(
        expr=(
            sum(model.x[i, 7] for i in nodes if i != 7)
            - sum(model.x[7, j] for j in nodes if j != 7)
            == model.sink_excess
        )
    )

    def transit_balance_rule(network, k):
        return (
            sum(network.x[i, k] for i in nodes if i != k)
            == sum(network.x[k, j] for j in nodes if j != k)
        )

    model.transit_balance = pyo.Constraint(
        model.transit_nodes, rule=transit_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.x[i, j]
            for i, j in edges
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