# IR: {"sets":{"centers":"0..3","stores":"0..7"},"params":{"opening_costs":"centers","transport_costs":"centers x stores","demands":"stores","capacities":"centers"},"variables":{"opened[center]":"Binary","shipment[center,store]":"NonNegativeReals"},"constraints":["For each store: sum_center shipment[center,store] = demands[store]","For each center: sum_store shipment[center,store] <= capacities[center] * opened[center]"],"objective":"Minimize sum_center opening_costs[center]*opened[center] + sum_center,store transport_costs[center,store]*shipment[center,store]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, 3)
    model.stores = pyo.RangeSet(0, 7)

    model.opening_costs = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: opening_costs[center],
    )
    model.transport_costs = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, center, store: transport_costs[center][store],
    )
    model.demands = pyo.Param(
        model.stores,
        initialize=lambda mdl, store: demands[store],
    )
    model.capacities = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: capacities[center],
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[center, store] for center in mdl.centers)
            == mdl.demands[store]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, center):
        return (
            sum(mdl.shipment[center, store] for store in mdl.stores)
            <= mdl.capacities[center] * mdl.opened[center]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_costs[center] * model.opened[center]
                for center in model.centers
            )
            + sum(
                model.transport_costs[center, store]
                * model.shipment[center, store]
                for center in model.centers
                for store in model.stores
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}