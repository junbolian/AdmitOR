# IR: {"sets":{"aircraft_types":[0,1,2,3,4],"routes":[0,1,2,3,4]},"params":{"aircraft_availability":"aircraft_types -> available units, supplied in params","route_demand":"routes -> required passengers, supplied in params","capacity":"aircraft_types x routes -> passengers per aircraft, supplied in params","operational_cost":"aircraft_types x routes -> cost per aircraft, supplied in params"},"variables":{"x[i,j]":"nonnegative integer aircraft assigned from type i to route j"},"constraints":["For each i: sum_j x[i,j] <= aircraft_availability[i]","For each j: sum_i capacity[i,j]*x[i,j] >= route_demand[j]"],"objective":"minimize sum_i sum_j operational_cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    operational_cost = params["operational_cost"]

    model = pyo.ConcreteModel()
    model.aircraft_types = pyo.RangeSet(0, 4)
    model.routes = pyo.RangeSet(0, 4)

    model.aircraft_availability = pyo.Param(
        model.aircraft_types,
        initialize=lambda mdl, i: aircraft_availability[i],
    )
    model.route_demand = pyo.Param(
        model.routes,
        initialize=lambda mdl, j: route_demand[j],
    )
    model.capacity = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: capacity[i][j],
    )
    model.operational_cost = pyo.Param(
        model.aircraft_types,
        model.routes,
        initialize=lambda mdl, i, j: operational_cost[i][j],
    )

    model.x = pyo.Var(
        model.aircraft_types,
        model.routes,
        domain=pyo.NonNegativeIntegers,
    )

    def availability_rule(mdl, i):
        return (
            sum(mdl.x[i, j] for j in mdl.routes)
            <= mdl.aircraft_availability[i]
        )

    model.availability_constraints = pyo.Constraint(
        model.aircraft_types,
        rule=availability_rule,
    )

    def demand_rule(mdl, j):
        return (
            sum(
                mdl.capacity[i, j] * mdl.x[i, j]
                for i in mdl.aircraft_types
            )
            >= mdl.route_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.routes,
        rule=demand_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.operational_cost[i, j] * model.x[i, j]
            for i in model.aircraft_types
            for j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}