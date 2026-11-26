# IR: {"sets":{"C":"0..3","S":"0..7"},"params":{"opening_cost":"C -> real, params['opening_cost'][c]","transport_cost":"C x S -> real, params['transport_cost'][c][s]","demand":"S -> nonnegative real, params['demand'][s]","capacity":"C -> nonnegative real, params['capacity'][c]"},"variables":{"opened[c]":"binary","shipment[c,s]":"nonnegative continuous"},"constraints":["For each s: sum_c shipment[c,s] = demand[s]","For each c: sum_s shipment[c,s] <= capacity[c] * opened[c]"],"objective":"Minimize sum_c opening_cost[c]*opened[c] + sum_c,s transport_cost[c,s]*shipment[c,s]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-4/8 sequences and a 4-by-8 transport-cost array."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 3)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={c: opening_cost[c] for c in model.centers},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (c, s): transport_cost[c][s]
            for c in model.centers
            for s in model.stores
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={s: demand[s] for s in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={c: capacity[c] for c in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(problem, s):
        return (
            sum(problem.shipment[c, s] for c in problem.centers)
            == problem.demand[s]
        )

    def capacity_rule(problem, c):
        return (
            sum(problem.shipment[c, s] for s in problem.stores)
            <= problem.capacity[c] * problem.opened[c]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[c] * model.opened[c]
            for c in model.centers
        )
        + sum(
            model.transport_cost[c, s] * model.shipment[c, s]
            for c in model.centers
            for s in model.stores
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}