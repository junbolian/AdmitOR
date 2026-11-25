# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},"params":{"supply":"params['supply'][i][k], nonnegative, O x P","demand":"params['demand'][j][k], nonnegative, D x P","cost":"params['cost'][i][j][k], real, O x D x P","capacity":"params['capacity'][i][j], nonnegative, O x D"},"variables":{"shipment[i,j,k]":"nonnegative continuous, O x D x P"},"constraints":["For each i,k: sum_j shipment[i,j,k] = supply[i,k]","For each j,k: sum_i shipment[i,j,k] = demand[j,k]","For each i,j: sum_k shipment[i,j,k] <= capacity[i,j]"],"objective":"Minimize sum_i,j,k cost[i,j,k] * shipment[i,j,k]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.origins,
        model.products,
        initialize=lambda mdl, i, k: supply[i][k],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize=lambda mdl, j, k: demand[j][k],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize=lambda mdl, i, j, k: cost[i][j][k],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i, k):
        return (
            sum(mdl.shipment[i, j, k] for j in mdl.destinations)
            == mdl.supply[i, k]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, model.products, rule=supply_rule
    )

    def demand_rule(mdl, j, k):
        return (
            sum(mdl.shipment[i, j, k] for i in mdl.origins)
            == mdl.demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, model.products, rule=demand_rule
    )

    def capacity_rule(mdl, i, j):
        return (
            sum(mdl.shipment[i, j, k] for k in mdl.products)
            <= mdl.capacity[i, j]
        )

    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j, k] * model.shipment[i, j, k]
            for i in model.origins
            for j in model.destinations
            for k in model.products
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