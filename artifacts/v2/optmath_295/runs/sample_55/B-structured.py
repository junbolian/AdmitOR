# IR: {"sets":{"origins":"0..10","destinations":"0..11"},"params":{"supply":"nonnegative real[origins], from params['supply']","demand":"nonnegative real[destinations], from params['demand']","transport_cost":"real[origins,destinations], from params['transport_cost']"},"variables":{"shipment":"nonnegative continuous[origins,destinations]"},"constraints":["For each origin i: sum_j shipment[i,j] == supply[i] (all supplies fully utilized).","For each destination j: sum_i shipment[i,j] == demand[j]."],"objective":"Minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 10)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(current_model, i):
        return (
            sum(
                current_model.shipment[i, j]
                for j in current_model.destinations
            )
            == current_model.supply[i]
        )

    def demand_rule(current_model, j):
        return (
            sum(
                current_model.shipment[i, j]
                for i in current_model.origins
            )
            == current_model.demand[j]
        )

    model.supply_constraints = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_constraints = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi HiGHS raises this when no feasible solution can be loaded.
        # Unexpected solver errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}