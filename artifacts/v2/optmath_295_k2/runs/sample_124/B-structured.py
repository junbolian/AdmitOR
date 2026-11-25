# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","capacity_limits":"params['capacity_limits'][i][j]","costs":"params['costs'][i][j]"},"variables":{"x[i,j]":"continuous nonnegative"},"constraints":["sum(x[i,j] for j in J) == supply[i] for i in I","sum(x[i,j] for i in I) == demand[j] for j in J","x[i,j] <= capacity_limits[i,j] for (i,j) in I x J"],"objective":"minimize sum(costs[i,j]*x[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]
    costs = params["costs"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 7)
    model.J = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.I,
        initialize={i: supply[i] for i in model.I},
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: demand[j] for j in model.J},
    )
    model.capacity_limits = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): capacity_limits[i][j]
            for i in model.I
            for j in model.J
        },
    )
    model.costs = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): costs[i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def supply_rule(instance, i):
        return (
            sum(instance.x[i, j] for j in instance.J)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.x[i, j] for i in instance.I)
            == instance.demand[j]
        )

    def capacity_rule(instance, i, j):
        return instance.x[i, j] <= instance.capacity_limits[i, j]

    model.supply_balance = pyo.Constraint(model.I, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.J, rule=demand_rule)
    model.assignment_limits = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}