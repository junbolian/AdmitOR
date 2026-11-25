# IR: {"sets":{"H":[0,1,2],"C":[3,4,5,6],"N":[0,1,2,3,4,5,6],"A":"H x C"},"params":{"supply":["supply_0","supply_1","supply_2"],"demand":["demand_3","demand_4","demand_5","demand_6"],"capacity":["cap_0_3","cap_0_4","cap_0_5","cap_0_6","cap_1_3","cap_1_4","cap_1_5","cap_1_6","cap_2_3","cap_2_4","cap_2_5","cap_2_6"],"cost":["cost_0_3","cost_0_4","cost_0_5","cost_0_6","cost_1_3","cost_1_4","cost_1_5","cost_1_6","cost_2_3","cost_2_4","cost_2_5","cost_2_6"],"coordinates":["coord_x","coord_y"],"domains":{"supply":"nonnegative real","demand":"nonnegative real","capacity":"nonnegative real","cost":"real","coordinates":"real metadata, indexed by N"}},"variables":{"shipment[h,c]":"nonnegative continuous, (h,c) in A"},"constraints":["sum(c in C) shipment[h,c] = supply[h], h in H","sum(h in H) shipment[h,c] = demand[c], c in C","shipment[h,c] <= capacity[h,c], (h,c) in A"],"objective":"minimize sum((h,c) in A) cost[h,c] * shipment[h,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.hubs = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.clinics = pyo.Set(initialize=[3, 4, 5, 6], ordered=True)
    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (hub, clinic)
            for hub in model.hubs
            for clinic in model.clinics
        ],
        ordered=True,
    )

    model.supply = pyo.Param(
        model.hubs,
        initialize={
            hub: params[f"supply_{hub}"]
            for hub in model.hubs
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.clinics,
        initialize={
            clinic: params[f"demand_{clinic}"]
            for clinic in model.clinics
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (hub, clinic): params[f"cap_{hub}_{clinic}"]
            for hub, clinic in model.arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={
            (hub, clinic): params[f"cost_{hub}_{clinic}"]
            for hub, clinic in model.arcs
        },
        within=pyo.Reals,
    )

    # Coordinates are supplied metadata; corridor costs are explicit inputs.
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]
    model.coord_x = pyo.Param(
        model.nodes,
        initialize={node: coord_x[node] for node in model.nodes},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.nodes,
        initialize={node: coord_y[node] for node in model.nodes},
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(current_model, hub):
        return (
            sum(
                current_model.shipment[hub, clinic]
                for clinic in current_model.clinics
            )
            == current_model.supply[hub]
        )

    model.supply_balance = pyo.Constraint(
        model.hubs,
        rule=supply_balance_rule,
    )

    def demand_balance_rule(current_model, clinic):
        return (
            sum(
                current_model.shipment[hub, clinic]
                for hub in current_model.hubs
            )
            == current_model.demand[clinic]
        )

    model.demand_balance = pyo.Constraint(
        model.clinics,
        rule=demand_balance_rule,
    )

    def corridor_limit_rule(current_model, hub, clinic):
        return (
            current_model.shipment[hub, clinic]
            <= current_model.capacity[hub, clinic]
        )

    model.corridor_limit = pyo.Constraint(
        model.arcs,
        rule=corridor_limit_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[hub, clinic] * model.shipment[hub, clinic]
            for hub, clinic in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}