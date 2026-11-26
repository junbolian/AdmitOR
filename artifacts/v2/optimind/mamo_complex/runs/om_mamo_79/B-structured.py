# IR: {"sets":{"R":[0,1,2,3,4],"A":"R x R"},"params":{"cost_matrix":"5x5 unit relocation costs; diagonal zero","supply":"available cars by region","demand":"required cars by region"},"variables":{"cars[i,j]":"nonnegative integer; cars originating in i and allocated to j, including cars retained when i=j"},"constraints":["For each i: sum_j cars[i,j] <= supply[i]","For each j: sum_i cars[i,j] >= demand[j]"],"objective":"Minimize sum_(i,j) cost_matrix[i,j] * cars[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    supply = params["supply"]
    demand = params["demand"]

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 4)

    model.unit_cost = pyo.Param(
        model.regions,
        model.regions,
        initialize=lambda mdl, origin, destination: cost_matrix[origin][destination],
    )
    model.available_cars = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: supply[region],
    )
    model.required_cars = pyo.Param(
        model.regions,
        initialize=lambda mdl, region: demand[region],
    )

    model.cars = pyo.Var(
        model.regions,
        model.regions,
        domain=pyo.NonNegativeIntegers,
    )

    def supply_rule(mdl, origin):
        return (
            sum(mdl.cars[origin, destination] for destination in mdl.regions)
            <= mdl.available_cars[origin]
        )

    model.supply_limits = pyo.Constraint(model.regions, rule=supply_rule)

    def demand_rule(mdl, destination):
        return (
            sum(mdl.cars[origin, destination] for origin in mdl.regions)
            >= mdl.required_cars[destination]
        )

    model.demand_requirements = pyo.Constraint(model.regions, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination] * model.cars[origin, destination]
            for origin in model.regions
            for destination in model.regions
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Still determine success solely by objective-value availability.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}