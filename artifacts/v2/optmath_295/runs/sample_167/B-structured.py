# IR: {
#   "sets": {"I": "range(n_producers)", "J": "range(n_contracts)"},
#   "params": {"cost": "real[I,J]", "capacity": "nonnegative_real[I]", "demand": "nonnegative_real[J]", "min_contributors": "nonnegative_integer[J]", "min_delivery": "nonnegative_real[I]", "n_producers": "positive_integer", "n_contracts": "positive_integer"},
#   "variables": {"delivery[I,J]": "nonnegative_continuous", "contributes[I,J]": "binary"},
#   "constraints": [
#     "producer_capacity[i]: sum(delivery[i,j] for j in J) <= capacity[i], for i in I",
#     "contract_demand[j]: sum(delivery[i,j] for i in I) >= demand[j], for j in J",
#     "contributor_requirement[j]: sum(contributes[i,j] for i in I) >= min_contributors[j], for j in J",
#     "minimum_shipment[i,j]: delivery[i,j] >= min_delivery[i]*contributes[i,j], for (i,j) in I x J",
#     "shipment_activation[i,j]: delivery[i,j] <= capacity[i]*contributes[i,j], for (i,j) in I x J"
#   ],
#   "objective": "minimize sum(cost[i,j]*delivery[i,j] for (i,j) in I x J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_producers = params["n_producers"]
    n_contracts = params["n_contracts"]
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=range(n_producers), ordered=True)
    model.J = pyo.Set(initialize=range(n_contracts), ordered=True)

    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda md, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.I,
        initialize=lambda md, i: capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda md, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.J,
        initialize=lambda md, j: min_contributors[j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.I,
        initialize=lambda md, i: min_delivery[i],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.I, model.J, domain=pyo.Binary
    )

    model.producer_capacity = pyo.Constraint(
        model.I,
        rule=lambda md, i: (
            sum(md.delivery[i, j] for j in md.J) <= md.capacity[i]
        ),
    )
    model.contract_demand = pyo.Constraint(
        model.J,
        rule=lambda md, j: (
            sum(md.delivery[i, j] for i in md.I) >= md.demand[j]
        ),
    )
    model.contributor_requirement = pyo.Constraint(
        model.J,
        rule=lambda md, j: (
            sum(md.contributes[i, j] for i in md.I)
            >= md.min_contributors[j]
        ),
    )
    model.minimum_shipment = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda md, i, j: (
            md.delivery[i, j]
            >= md.min_delivery[i] * md.contributes[i, j]
        ),
    )
    model.shipment_activation = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda md, i, j: (
            md.delivery[i, j]
            <= md.capacity[i] * md.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.delivery[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if not str(exc).startswith(
            "A feasible solution was not found, so no solution can be loaded."
        ):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}