# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"cost":"real[P,C]","capacity":"nonnegative_real[P]","demand":"nonnegative_real[C]","min_producers":"nonnegative_integer[C]","min_delivery":"nonnegative_real[P]"},"variables":{"delivery":"nonnegative_real[P,C]","assigned":"binary[P,C]"},"constraints":["forall i in P: sum(delivery[i,j] for j in C) <= capacity[i]","forall j in C: sum(delivery[i,j] for i in P) >= demand[j]","forall j in C: sum(assigned[i,j] for i in P) >= min_producers[j]","forall i in P,j in C: delivery[i,j] >= min_delivery[i]*assigned[i,j]","forall i in P,j in C: delivery[i,j] <= capacity[i]*assigned[i,j]"],"objective":"minimize sum(cost[i,j]*delivery[i,j] for i in P,j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using cost[i][j] and producer/contract-indexed parameter sequences."""
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_producers = pyo.Param(
        model.C,
        initialize=lambda mdl, j: params["min_producers"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize=lambda mdl, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.assigned = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.producer_capacity = pyo.Constraint(
        model.P,
        rule=lambda mdl, i: sum(mdl.delivery[i, j] for j in mdl.C)
        <= mdl.capacity[i],
    )
    model.contract_demand = pyo.Constraint(
        model.C,
        rule=lambda mdl, j: sum(mdl.delivery[i, j] for i in mdl.P)
        >= mdl.demand[j],
    )
    model.producer_cardinality = pyo.Constraint(
        model.C,
        rule=lambda mdl, j: sum(mdl.assigned[i, j] for i in mdl.P)
        >= mdl.min_producers[j],
    )
    model.minimum_assigned_delivery = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, i, j: mdl.delivery[i, j]
        >= mdl.min_delivery[i] * mdl.assigned[i, j],
    )
    model.assignment_capacity_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, i, j: mdl.delivery[i, j]
        <= mdl.capacity[i] * mdl.assigned[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.delivery[i, j]
            for i in model.P
            for j in model.C
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