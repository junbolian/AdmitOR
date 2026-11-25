# IR: {"sets":{"N":"{0,...,7}","A":"[(i,j) for i in N for j in N if i != j], in lexicographic order","I":"{1,...,6}"},"params":{"cost":"56 route costs indexed by A in order, from params['cost']","net_outflow_node_0":"params['net_outflow_node_0']","net_inflow_node_7":"params['net_inflow_node_7']"},"variables":{"x[i,j]":"binary, for (i,j) in A"},"constraints":["sum(x[0,j] for j != 0) - sum(x[j,0] for j != 0) = net_outflow_node_0","sum(x[j,7] for j != 7) - sum(x[7,j] for j != 7) = net_inflow_node_7","sum(x[j,i] for j != i) = sum(x[i,j] for j != i), for i in I"],"objective":"minimize sum(cost[i,j] * x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(8)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    route_costs = params["cost"]
    required_outflow = params["net_outflow_node_0"]
    required_inflow = params["net_inflow_node_7"]

    if len(route_costs) != len(arcs):
        raise ValueError("params['cost'] must contain exactly 56 route costs.")

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.I = pyo.Set(initialize=range(1, 7), ordered=True)

    model.route_cost = pyo.Param(
        model.A,
        initialize={arc: route_costs[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.required_outflow = pyo.Param(
        initialize=required_outflow,
        within=pyo.Reals,
    )
    model.required_inflow = pyo.Param(
        initialize=required_inflow,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in model.N if j != 0)
            - sum(model.x[j, 0] for j in model.N if j != 0)
            == model.required_outflow
        )
    )

    model.destination_balance = pyo.Constraint(
        expr=(
            sum(model.x[j, 7] for j in model.N if j != 7)
            - sum(model.x[7, j] for j in model.N if j != 7)
            == model.required_inflow
        )
    )

    def intermediate_balance_rule(block, i):
        return (
            sum(block.x[j, i] for j in block.N if j != i)
            == sum(block.x[i, j] for j in block.N if j != i)
        )

    model.intermediate_balance = pyo.Constraint(
        model.I,
        rule=intermediate_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.x[i, j]
            for i, j in model.A
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