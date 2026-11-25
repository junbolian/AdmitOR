# IR: {"sets":{"N":"0..6","A":"{(i,j) in N x N: i != j}"},"params":{"cost_matrix":"arc costs read from params; diagonal unused","source_supply":"required net outflow at node 0, read from params","sink_demand":"required net inflow at node 6, read from params"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = source_supply","sum_i x[i,6] - sum_j x[6,j] = sink_demand","sum_j x[k,j] - sum_i x[i,k] = 0 for k in {1,...,5}; all sums exclude self-arcs"],"objective":"minimize sum_(i,j in A) cost_matrix[i][j] * x[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 6)
    model.intermediate_nodes = pyo.RangeSet(1, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params["cost_matrix"][i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["source_supply"],
        within=pyo.Reals,
    )
    model.sink_demand = pyo.Param(
        initialize=params["sink_demand"],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.x[0, j] for j in model.nodes if j != 0)
            - sum(model.x[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )

    model.sink_balance = pyo.Constraint(
        expr=(
            sum(model.x[i, 6] for i in model.nodes if i != 6)
            - sum(model.x[6, j] for j in model.nodes if j != 6)
            == model.sink_demand
        )
    )

    def intermediate_balance_rule(instance, k):
        return (
            sum(instance.x[k, j] for j in instance.nodes if j != k)
            - sum(instance.x[i, k] for i in instance.nodes if i != k)
            == 0
        )

    model.intermediate_balance = pyo.Constraint(
        model.intermediate_nodes,
        rule=intermediate_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}