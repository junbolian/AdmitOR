# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j) in N x N : i != j}"},"params":{"supply_node_0":"params['supply_node_0']","demand_node_6":"params['demand_node_6']","cost[i,j]":"params['cost_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"x[i,j]":{"type":"binary","index":"A"}},"constraints":["sum(j != 0, x[0,j]) - sum(j != 0, x[j,0]) = supply_node_0","for i in {1,2,3,4,5}: sum(j != i, x[i,j]) - sum(j != i, x[j,i]) = 0","sum(j != 6, x[6,j]) - sum(j != 6, x[j,6]) = -demand_node_6"],"objective":{"sense":"minimize","expression":"sum((i,j) in A, cost[i,j]*x[i,j])"}}

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

    model.supply_node_0 = pyo.Param(
        initialize=params["supply_node_0"], within=pyo.Reals
    )
    model.demand_node_6 = pyo.Param(
        initialize=params["demand_node_6"], within=pyo.Reals
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def balance_rule(network, i):
        net_outflow = (
            sum(network.x[i, j] for j in network.nodes if j != i)
            - sum(network.x[j, i] for j in network.nodes if j != i)
        )
        if i == 0:
            return net_outflow == network.supply_node_0
        if i == 6:
            return net_outflow == -network.demand_node_6
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.x[i, j]
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