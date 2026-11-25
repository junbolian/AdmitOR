# IR: {"sets":{"I":"0..6","J":"0..6","P":"0..1"},"params":{"supply":"row-major flatten(params['supply'])[2*i+p]","demand":"row-major flatten(params['demand'])[2*j+p]","cost":"row-major flatten(params['cost'])[14*i+2*j+p]","cap":"row-major flatten(params['cap'])[7*i+j]"},"variables":{"x[i,j,p]":"nonnegative continuous"},"constraints":["sum_j x[i,j,p] = supply[i,p] for each i,p","sum_i x[i,j,p] = demand[j,p] for each j,p","sum_p x[i,j,p] <= cap[i,j] for each i,j"],"objective":"minimize sum_i,j,p cost[i,j,p]*x[i,j,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _flatten(values):
    """Flatten flat or nested lists/tuples in row-major order."""
    flattened = []
    for value in values:
        if isinstance(value, (list, tuple)):
            flattened.extend(_flatten(value))
        else:
            flattened.append(value)
    return flattened


def solve(params):
    supply = _flatten(params["supply"])
    demand = _flatten(params["demand"])
    cost = _flatten(params["cost"])
    cap = _flatten(params["cap"])

    if (
        len(supply) != 14
        or len(demand) != 14
        or len(cost) != 98
        or len(cap) != 49
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 6)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.I,
        model.P,
        initialize={
            (i, p): supply[2 * i + p]
            for i in model.I
            for p in model.P
        },
    )
    model.demand = pyo.Param(
        model.J,
        model.P,
        initialize={
            (j, p): demand[2 * j + p]
            for j in model.J
            for p in model.P
        },
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        model.P,
        initialize={
            (i, j, p): cost[14 * i + 2 * j + p]
            for i in model.I
            for j in model.J
            for p in model.P
        },
    )
    model.cap = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): cap[7 * i + j]
            for i in model.I
            for j in model.J
        },
    )

    model.x = pyo.Var(
        model.I, model.J, model.P, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, i, p):
        return sum(mdl.x[i, j, p] for j in mdl.J) == mdl.supply[i, p]

    def demand_rule(mdl, j, p):
        return sum(mdl.x[i, j, p] for i in mdl.I) == mdl.demand[j, p]

    def capacity_rule(mdl, i, j):
        return sum(mdl.x[i, j, p] for p in mdl.P) <= mdl.cap[i, j]

    model.supply_balance = pyo.Constraint(
        model.I, model.P, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.J, model.P, rule=demand_rule
    )
    model.route_capacity = pyo.Constraint(
        model.I, model.J, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j, p] * model.x[i, j, p]
            for i in model.I
            for j in model.J
            for p in model.P
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