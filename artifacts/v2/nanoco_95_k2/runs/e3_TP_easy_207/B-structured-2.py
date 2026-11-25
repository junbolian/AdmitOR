# IR: {"sets":{"H":[0,1,2],"D":[3,4,5,6],"A":"H x D"},"params":{"supply[h]":"params[f'supply_hub{h}']","demand[d]":"params[f'demand_area{d}']","capacity[h,d]":"params[f'capacity_arc_{h}_{d}']","cost[h,d]":"params[f'cost_arc_{h}_{d}']"},"variables":{"shipment[h,d]":{"type":"continuous","lower":0,"upper":"capacity[h,d]"}},"constraints":["For each h in H: sum(shipment[h,d] for d in D) = supply[h]","For each d in D: sum(shipment[h,d] for h in H) = demand[d]"],"objective":{"sense":"minimize","expression":"sum(cost[h,d] * shipment[h,d] for (h,d) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.areas = pyo.Set(initialize=[3, 4, 5, 6], ordered=True)
    model.corridors = pyo.Set(
        dimen=2,
        initialize=[
            (hub, area)
            for hub in model.hubs
            for area in model.areas
        ],
        ordered=True,
    )

    model.stock = pyo.Param(
        model.hubs,
        initialize={
            hub: params[f"supply_hub{hub}"]
            for hub in model.hubs
        },
        within=pyo.Reals,
    )
    model.requirement = pyo.Param(
        model.areas,
        initialize={
            area: params[f"demand_area{area}"]
            for area in model.areas
        },
        within=pyo.Reals,
    )
    model.payload_limit = pyo.Param(
        model.corridors,
        initialize={
            (hub, area): params[f"capacity_arc_{hub}_{area}"]
            for hub, area in model.corridors
        },
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.corridors,
        initialize={
            (hub, area): params[f"cost_arc_{hub}_{area}"]
            for hub, area in model.corridors
        },
        within=pyo.Reals,
    )

    def shipment_bounds(problem, hub, area):
        return 0, problem.payload_limit[hub, area]

    model.shipment = pyo.Var(
        model.corridors,
        domain=pyo.NonNegativeReals,
        bounds=shipment_bounds,
    )

    def dispatch_rule(problem, hub):
        return (
            sum(problem.shipment[hub, area] for area in problem.areas)
            == problem.stock[hub]
        )

    model.dispatch_balance = pyo.Constraint(
        model.hubs,
        rule=dispatch_rule,
    )

    def delivery_rule(problem, area):
        return (
            sum(problem.shipment[hub, area] for hub in problem.hubs)
            == problem.requirement[area]
        )

    model.delivery_balance = pyo.Constraint(
        model.areas,
        rule=delivery_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[hub, area] * model.shipment[hub, area]
            for hub, area in model.corridors
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}