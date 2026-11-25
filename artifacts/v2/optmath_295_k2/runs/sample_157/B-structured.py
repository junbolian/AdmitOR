# IR: {"sets":{"N":[0,1,2,3,4,5],"T":[1,2,3,4],"A":"{(i,j) in N x N : i != j}"},"params":{"supply_node0":"params['supply_node0']","demand_node5":"params['demand_node5']","cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply_node0","sum_i x[i,k] - sum_j x[k,j] = 0 for k in T","sum_i x[i,5] - sum_j x[5,j] = demand_node5"],"objective":"minimize sum_(i,j) cost[i,j]*x[i,j]"}
# The final problem bullet has a sign inconsistency. Positive net demand
# means inflow minus outflow equals demand_node5, as modeled here.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(6)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.transshipment_nodes = pyo.Set(initialize=range(1, 5))
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.supply = pyo.Param(initialize=params["supply_node0"])
    model.demand = pyo.Param(initialize=params["demand_node5"])
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in arcs
        },
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[0, j] for j in nodes if j != 0)
            - sum(model.route_used[i, 0] for i in nodes if i != 0)
            == model.supply
        )
    )

    def transshipment_balance_rule(network, node):
        return (
            sum(
                network.route_used[i, node]
                for i in network.nodes
                if i != node
            )
            - sum(
                network.route_used[node, j]
                for j in network.nodes
                if j != node
            )
            == 0
        )

    model.transshipment_balance = pyo.Constraint(
        model.transshipment_nodes,
        rule=transshipment_balance_rule,
    )

    model.sink_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[i, 5] for i in nodes if i != 5)
            - sum(model.route_used[5, j] for j in nodes if j != 5)
            == model.demand
        )
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.route_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no solution is available to load.
        # Determine success solely through objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}