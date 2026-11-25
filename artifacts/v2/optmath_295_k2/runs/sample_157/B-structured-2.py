# IR: {"sets":{"N":[0,1,2,3,4,5],"A":"{(i,j) in N x N : i != j}","T":[1,2,3,4]},"params":{"supply_node0":"params['supply_node0']","demand_node5":"params['demand_node5']","cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply_node0","sum_i x[i,k] - sum_j x[k,j] = 0 for k in T","sum_i x[i,5] - sum_j x[5,j] = demand_node5"],"objective":"minimize sum_(i,j) cost[i,j] * x[i,j]"}
# Demand uses the parameter's stated meaning: inflow minus outflow.
# The final problem bullet's negative demand sign contradicts that meaning.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(6)
            for j in range(6)
            if i != j
        ],
        ordered=True,
    )
    model.transshipment_nodes = pyo.Set(
        initialize=range(1, 5), ordered=True
    )

    model.supply = pyo.Param(initialize=params["supply_node0"])
    model.demand = pyo.Param(initialize=params["demand_node5"])
    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in model.nodes if j != 0)
            - sum(model.x[i, 0] for i in model.nodes if i != 0)
            == model.supply
        )
    )

    def transshipment_balance_rule(network, k):
        return (
            sum(network.x[i, k] for i in network.nodes if i != k)
            - sum(network.x[k, j] for j in network.nodes if j != k)
            == 0
        )

    model.transshipment_balance = pyo.Constraint(
        model.transshipment_nodes,
        rule=transshipment_balance_rule,
    )

    model.destination_balance = pyo.Constraint(
        expr=(
            sum(model.x[i, 5] for i in model.nodes if i != 5)
            - sum(model.x[5, j] for j in model.nodes if j != 5)
            == model.demand
        )
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}