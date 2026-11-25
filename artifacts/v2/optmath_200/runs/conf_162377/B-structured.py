# IR: {"sets":{"origins":[0,1,2,3],"destinations":[0,1,2,3]},"params":{"supply":"nonnegative real[origins]","demand":"nonnegative real[destinations]","cost":"real[origins,destinations]","capacity":"nonnegative real[origins,destinations]"},"variables":{"shipment":"nonnegative continuous[origins,destinations]"},"constraints":["For each origin i: sum_j shipment[i,j] = supply[i]","For each destination j: sum_i shipment[i,j] = demand[j]","For each arc (i,j): shipment[i,j] <= capacity[i,j]"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 3)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: params["supply"][i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: params["demand"][j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.destinations)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.origins)
            == instance.demand[j]
        )

    def capacity_rule(instance, i, j):
        return instance.shipment[i, j] <= instance.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.arc_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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