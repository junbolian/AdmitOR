# IR: {"sets":{"DC":"0..5","Store":"0..8"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input vectors and a row-major cost matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.dc_set = pyo.RangeSet(0, 5)
    model.store_set = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: opening_cost[i],
    )
    model.transport_cost = pyo.Param(
        model.dc_set,
        model.store_set,
        initialize=lambda mdl, i, j: transport_cost[i][j],
    )
    model.demand = pyo.Param(
        model.store_set,
        initialize=lambda mdl, j: demand[j],
    )
    model.capacity = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: capacity[i],
    )

    model.opened = pyo.Var(model.dc_set, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.dc_set,
        model.store_set,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.shipment[i, j] for i in mdl.dc_set
        ) == mdl.demand[j]

    model.demand_constraints = pyo.Constraint(
        model.store_set, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return sum(
            mdl.shipment[i, j] for j in mdl.store_set
        ) <= mdl.capacity[i] * mdl.opened[i]

    model.capacity_constraints = pyo.Constraint(
        model.dc_set, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.dc_set
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.dc_set
                for j in model.store_set
            )
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