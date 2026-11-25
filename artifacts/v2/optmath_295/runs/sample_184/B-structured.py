# IR: {"sets":{"O":[0,1,2,3],"D":[0,1,2,3,4],"P":[0,1]},
# "params":{"supply":"params['supply'][o][p]","demand":"params['demand'][d][p]","cost":"params['cost'][o][d][p]","capacity":"params['capacity'][o][d]"},
# "variables":{"shipment[o,d,p]":{"type":"NonNegativeReals"}},
# "constraints":["sum_d shipment[o,d,p] = supply[o,p] for all o,p","sum_o shipment[o,d,p] = demand[d,p] for all d,p","sum_p shipment[o,d,p] <= capacity[o,d] for all o,d"],
# "objective":"minimize sum_{o,d,p} cost[o,d,p] * shipment[o,d,p]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using nested arrays indexed as specified in the IR."""
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
        initialize=lambda mdl, origin, product: supply[origin][product],
    )
    model.demand = pyo.Param(
        model.destinations,
        model.products,
        initialize=lambda mdl, destination, product: demand[destination][product],
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        model.products,
        initialize=lambda mdl, origin, destination, product: (
            cost[origin][destination][product]
        ),
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: capacity[origin][destination],
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, origin, product):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for destination in mdl.destinations
            )
            == mdl.supply[origin, product]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, model.products, rule=supply_rule
    )

    def demand_rule(mdl, destination, product):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for origin in mdl.origins
            )
            == mdl.demand[destination, product]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, model.products, rule=demand_rule
    )

    def capacity_rule(mdl, origin, destination):
        return (
            sum(
                mdl.shipment[origin, destination, product]
                for product in mdl.products
            )
            <= mdl.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination, product]
            * model.shipment[origin, destination, product]
            for origin in model.origins
            for destination in model.destinations
            for product in model.products
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