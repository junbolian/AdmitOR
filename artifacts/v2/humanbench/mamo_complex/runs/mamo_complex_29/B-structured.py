# IR: {"sets":{"R":[0,1,2,3,4]},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","transport_cost":"transport_cost[i,j] from params['transport_cost']"},"variables":{"shipment[i,j]":"nonnegative real; initial supply from i allocated to demand at j, including local use when i=j"},"constraints":["For each i: sum_j shipment[i,j] <= supply[i].","For each j: sum_i shipment[i,j] = demand[j]."],"objective":"Minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize transportation cost; unused initial supply is permitted."""
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 4)

    model.supply_units = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: supply[region],
        within=pyo.NonNegativeReals,
    )
    model.demand_units = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: demand[region],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.regions,
        model.regions,
        initialize=lambda mdl, origin, destination: (
            transport_cost[origin][destination]
        ),
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.regions,
        model.regions,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, origin):
        return (
            sum(
                mdl.shipment[origin, destination]
                for destination in mdl.regions
            )
            <= mdl.supply_units[origin]
        )

    model.supply_limits = pyo.Constraint(
        model.regions,
        rule=supply_rule,
    )

    def demand_rule(mdl, destination):
        return (
            sum(
                mdl.shipment[origin, destination]
                for origin in mdl.regions
            )
            == mdl.demand_units[destination]
        )

    model.demand_requirements = pyo.Constraint(
        model.regions,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.regions
            for destination in model.regions
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}