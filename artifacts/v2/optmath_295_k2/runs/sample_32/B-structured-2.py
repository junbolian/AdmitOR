# IR: {"sets":{"origins":[0,1,2,3,4],"destinations":[0,1,2,3,4]},"params":{"supply_origin":"nonnegative vector indexed by origins","demand_destination":"nonnegative vector indexed by destinations","cost_matrix":"real matrix indexed by origins,destinations","capacity_matrix":"nonnegative matrix indexed by origins,destinations"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] == supply_origin[i] for each origin i","sum_i shipment[i,j] == demand_destination[j] for each destination j","shipment[i,j] <= capacity_matrix[i][j] for each pair i,j"],"objective":"minimize sum_i sum_j cost_matrix[i][j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_origin = params["supply_origin"]
    demand_destination = params["demand_destination"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda model, i: supply_origin[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda model, j: demand_destination[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda model, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda model, i, j: capacity_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda model, i: sum(
            model.shipment[i, j] for j in model.destinations
        ) == model.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda model, j: sum(
            model.shipment[i, j] for i in model.origins
        ) == model.demand[j],
    )
    model.capacity_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda model, i, j: (
            model.shipment[i, j] <= model.route_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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