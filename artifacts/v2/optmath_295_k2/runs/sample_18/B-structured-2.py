# IR: {"sets":{"I":[0,1,2,3,4,5],"J":[0,1,2,3,4,5]},"params":{"supply":"nonnegative real[I], from params['supply'][i]","demand":"nonnegative real[J], from params['demand'][j]","cost_matrix":"real[I,J], from params['cost_matrix'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous, i in I, j in J"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for each i in I","sum(shipment[i,j] for i in I) == demand[j] for each j in J"],"objective":"minimize sum(cost_matrix[i,j] * shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I,
        initialize={i: supply[i] for i in model.I},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: demand[j] for j in model.J},
        within=pyo.NonNegativeReals,
    )
    model.cost_matrix = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): cost_matrix[i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.J)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.I)
            == instance.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_matrix[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}