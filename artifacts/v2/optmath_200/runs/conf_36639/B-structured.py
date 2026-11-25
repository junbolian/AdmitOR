# IR: {"sets":{"H":"{0,...,10} with cardinality params['num_hubs']=11","A":"{(i,j) in H x H: i != j}","I":"H \\ {0,10}"},"params":{"num_hubs":"params['num_hubs']","cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A","supply":"params['supply_hub0']","demand":"params['demand_hub10']"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":{"source_balance":"sum(j != 0, x[0,j]) - sum(i != 0, x[i,0]) = supply","sink_balance":"sum(i != 10, x[i,10]) - sum(j != 10, x[10,j]) = demand","intermediate_balance":"sum(j != h, x[h,j]) - sum(i != h, x[i,h]) = 0 for h in I"},"objective":"minimize sum((i,j) in A, cost[i,j] * x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_hubs = params["num_hubs"]
    if num_hubs != 11:
        return {"objective": None, "status": "invalid_num_hubs"}

    hubs = range(int(num_hubs))
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    model = pyo.ConcreteModel()

    model.num_hubs = pyo.Param(
        initialize=num_hubs,
        within=pyo.PositiveIntegers,
    )
    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.arcs = pyo.Set(
        initialize=arcs,
        dimen=2,
        ordered=True,
    )
    model.intermediate_hubs = pyo.Set(
        initialize=[h for h in hubs if h not in (0, 10)],
        ordered=True,
    )

    model.route_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )
    model.source_supply = pyo.Param(
        initialize=params["supply_hub0"],
        within=pyo.Reals,
    )
    model.destination_demand = pyo.Param(
        initialize=params["demand_hub10"],
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    model.source_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[0, j] for j in hubs if j != 0)
            - sum(model.route_used[i, 0] for i in hubs if i != 0)
            == model.source_supply
        )
    )

    model.sink_balance = pyo.Constraint(
        expr=(
            sum(model.route_used[i, 10] for i in hubs if i != 10)
            - sum(model.route_used[10, j] for j in hubs if j != 10)
            == model.destination_demand
        )
    )

    def intermediate_balance_rule(instance, h):
        return (
            sum(instance.route_used[h, j] for j in instance.hubs if j != h)
            - sum(instance.route_used[i, h] for i in instance.hubs if i != h)
            == 0
        )

    model.intermediate_balance = pyo.Constraint(
        model.intermediate_hubs,
        rule=intermediate_balance_rule,
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors must propagate to the caller.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}