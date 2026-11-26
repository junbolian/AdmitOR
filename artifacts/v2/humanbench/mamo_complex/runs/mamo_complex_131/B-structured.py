# IR: {"sets":{"clinics":"0..5","arcs":"(i,j) in clinics x clinics where i != j"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][i]","transport_cost":"params['transport_cost'][i][j]"},"variables":{"transfer[i,j]":"NonNegativeReals","unused_supply[i]":"NonNegativeReals, bounded above by supply[i]; surplus excluded from demand allocation"},"constraints":["supply[i] - unused_supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) == demand[i], for each clinic i"],"objective":"minimize sum(transport_cost[i,j] * transfer[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.clinics = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.clinics
            for destination in model.clinics
            if origin != destination
        ],
    )

    model.initial_supply = pyo.Param(
        model.clinics,
        initialize={
            clinic: params["supply"][clinic]
            for clinic in model.clinics
        },
        within=pyo.NonNegativeReals,
    )
    model.required_supply = pyo.Param(
        model.clinics,
        initialize={
            clinic: params["demand"][clinic]
            for clinic in model.clinics
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params["transport_cost"][origin][destination]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    # Initial supply is available stock, not a requirement to use every unit.
    # Surplus remains unused while the allocated stock meets demand exactly.
    def unused_supply_bounds(instance, clinic):
        return (0, instance.initial_supply[clinic])

    model.unused_supply = pyo.Var(
        model.clinics,
        domain=pyo.NonNegativeReals,
        bounds=unused_supply_bounds,
    )

    def inventory_balance_rule(instance, clinic):
        incoming = sum(
            instance.transfer[origin, clinic]
            for origin in instance.clinics
            if origin != clinic
        )
        outgoing = sum(
            instance.transfer[clinic, destination]
            for destination in instance.clinics
            if destination != clinic
        )
        return (
            instance.initial_supply[clinic]
            - instance.unused_supply[clinic]
            + incoming
            - outgoing
            == instance.required_supply[clinic]
        )

    model.inventory_balance = pyo.Constraint(
        model.clinics,
        rule=inventory_balance_rule,
    )

    model.total_transport_cost = pyo.Objective(
        expr=sum(
            model.unit_transport_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_transport_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}