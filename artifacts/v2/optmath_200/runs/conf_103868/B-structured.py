# IR: {"sets":{"N":"0..7","A":"{(i,j) in N x N: i != j}"},"params":{"cost[i,j]":"params['cost_<i>_<j>'] for (i,j) in A","supply":"params['net_supply_node_0']","demand":"params['net_demand_node_7']"},"variables":{"x[i,j]":"binary for (i,j) in A"},"constraints":["sum_j x[0,j] - sum_i x[i,0] = supply","sum_i x[i,7] - sum_j x[7,j] = demand","sum_j x[k,j] - sum_i x[i,k] = 0 for k in 1..6"],"objective":"minimize sum_{(i,j) in A} cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["net_supply_node_0"], within=pyo.Reals
    )
    model.sink_demand = pyo.Param(
        initialize=params["net_demand_node_7"], within=pyo.Reals
    )
    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[0, j] for j in model.nodes if j != 0)
            - sum(model.route_used[i, 0] for i in model.nodes if i != 0)
            == model.source_supply
        )
    )
    model.sink_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[i, 7] for i in model.nodes if i != 7)
            - sum(model.route_used[7, j] for j in model.nodes if j != 7)
            == model.sink_demand
        )
    )

    def intermediate_balance_rule(instance, k):
        return (
            sum(instance.route_used[k, j] for j in instance.nodes if j != k)
            - sum(instance.route_used[i, k] for i in instance.nodes if i != k)
            == 0
        )

    model.intermediate_balance = pyo.Constraint(
        range(1, 7), rule=intermediate_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.route_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    # HiGHS raises RuntimeError when no feasible solution can be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}