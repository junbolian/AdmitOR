# IR: {"sets":{"DC":"0..6","STORE":"0..6"},"params":{"opening_cost":"nonnegative vector[7], indexed by DC","transport_cost":"nonnegative matrix[7][7], indexed by DC then STORE","demand":"nonnegative vector[7], indexed by STORE","capacity":"nonnegative vector[7], indexed by DC"},"variables":{"opened[dc]":"binary","shipment[dc,store]":"nonnegative continuous"},"constraints":["For each store: sum_dc shipment[dc,store] == demand[store]","For each dc: sum_store shipment[dc,store] <= capacity[dc] * opened[dc]"],"objective":"minimize sum_dc opening_cost[dc]*opened[dc] + sum_dc,store transport_cost[dc,store]*shipment[dc,store]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input vectors and a DC-by-store cost matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 6)
    model.STORE = pyo.RangeSet(0, 6)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={dc: opening_cost[dc] for dc in model.DC},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (dc, store): transport_cost[dc][store]
            for dc in model.DC
            for store in model.STORE
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={store: demand[store] for store in model.STORE},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={dc: capacity[dc] for dc in model.DC},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, store):
        return (
            sum(instance.shipment[dc, store] for dc in instance.DC)
            == instance.demand[store]
        )

    model.demand_requirement = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(instance, dc):
        return (
            sum(instance.shipment[dc, store] for store in instance.STORE)
            <= instance.capacity[dc] * instance.opened[dc]
        )

    model.capacity_limit = pyo.Constraint(model.DC, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[dc] * model.opened[dc]
                for dc in model.DC
            )
            + sum(
                model.transport_cost[dc, store] * model.shipment[dc, store]
                for dc in model.DC
                for store in model.STORE
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}