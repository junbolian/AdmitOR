# IR: {"sets":{"hubs":[0,1,2],"clinics":[3,4,5,6],"nodes":[0,1,2,3,4,5,6],"arcs":"hubs x clinics"},"params":{"supply":["supply_0","supply_1","supply_2"],"demand":["demand_3","demand_4","demand_5","demand_6"],"capacity":["cap_0_3","cap_0_4","cap_0_5","cap_0_6","cap_1_3","cap_1_4","cap_1_5","cap_1_6","cap_2_3","cap_2_4","cap_2_5","cap_2_6"],"cost":["cost_0_3","cost_0_4","cost_0_5","cost_0_6","cost_1_3","cost_1_4","cost_1_5","cost_1_6","cost_2_3","cost_2_4","cost_2_5","cost_2_6"],"coordinates":["coord_x","coord_y"],"coordinate_role":"node metadata; shipping costs are supplied directly"},"variables":{"shipment[i,j]":"nonnegative real for each arc"},"constraints":["sum(shipment[i,j] for j in clinics) == supply[i] for each hub i","sum(shipment[i,j] for i in hubs) == demand[j] for each clinic j","shipment[i,j] <= capacity[i,j] for each arc (i,j)"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: params["supply_2"],
    }
    demand = {
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
        6: params["demand_6"],
    }
    capacity = {
        (0, 3): params["cap_0_3"],
        (0, 4): params["cap_0_4"],
        (0, 5): params["cap_0_5"],
        (0, 6): params["cap_0_6"],
        (1, 3): params["cap_1_3"],
        (1, 4): params["cap_1_4"],
        (1, 5): params["cap_1_5"],
        (1, 6): params["cap_1_6"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (2, 5): params["cap_2_5"],
        (2, 6): params["cap_2_6"],
    }
    cost = {
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (0, 5): params["cost_0_5"],
        (0, 6): params["cost_0_6"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (1, 6): params["cost_1_6"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (2, 6): params["cost_2_6"],
    }
    coord_x = params["coord_x"]
    coord_y = params["coord_y"]

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
        model.hubs, initialize=supply, within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.clinics, initialize=demand, within=pyo.NonNegativeReals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacity, within=pyo.NonNegativeReals
    )
    model.shipping_cost = pyo.Param(
        model.arcs, initialize=cost, within=pyo.Reals
    )
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

    model.shipment = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def supply_balance_rule(mdl, hub):
        return (
            sum(mdl.shipment[hub, clinic] for clinic in mdl.clinics)
            == mdl.supply[hub]
        )

    def demand_balance_rule(mdl, clinic):
        return (
            sum(mdl.shipment[hub, clinic] for hub in mdl.hubs)
            == mdl.demand[clinic]
        )

    def corridor_capacity_rule(mdl, hub, clinic):
        return mdl.shipment[hub, clinic] <= mdl.capacity[hub, clinic]

    model.supply_balance = pyo.Constraint(
        model.hubs, rule=supply_balance_rule
    )
    model.demand_balance = pyo.Constraint(
        model.clinics, rule=demand_balance_rule
    )
    model.corridor_capacity = pyo.Constraint(
        model.arcs, rule=corridor_capacity_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.shipping_cost[hub, clinic] * model.shipment[hub, clinic]
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