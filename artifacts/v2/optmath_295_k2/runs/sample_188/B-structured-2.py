# IR: {"sets":{"origins":"0..7","destinations":"0..7"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","transport_cost":"transport_cost[i,j] from params['transport_cost']","pair_capacity":"pair_capacity[i,j] from params['pair_capacity']"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] == supply[i] for each origin i","sum_i shipment[i,j] == demand[j] for each destination j","shipment[i,j] <= pair_capacity[i,j] for each origin-destination pair"],"objective":"minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    pair_capacity = params["pair_capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 7)
    model.destinations = pyo.RangeSet(0, 7)

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
    model.pair_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): pair_capacity[i][j]
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

    def supply_rule(problem, i):
        return (
            sum(problem.shipment[i, j] for j in problem.destinations)
            == problem.supply[i]
        )

    def demand_rule(problem, j):
        return (
            sum(problem.shipment[i, j] for i in problem.origins)
            == problem.demand[j]
        )

    def capacity_rule(problem, i, j):
        return problem.shipment[i, j] <= problem.pair_capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
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
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}