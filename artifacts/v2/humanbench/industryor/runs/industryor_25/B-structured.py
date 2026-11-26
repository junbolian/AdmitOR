# IR: {"sets":{"mines":["A","B"],"areas":[1,2,3]},"params":{"supply_lower":{"A":"supply_A_lower","B":"supply_B_lower"},"demand":{"1":"demand_1","2":"demand_2","3":"demand_3"},"distance":{"A,1":"dist_A1","A,2":"dist_A2","A,3":"dist_A3","B,1":"dist_B1","B,2":"dist_B2","B,3":"dist_B3"}},"variables":{"shipment[mine,area]":"continuous nonnegative tons"},"constraints":["For each mine: sum_area shipment[mine,area] >= supply_lower[mine].","For each area: sum_mine shipment[mine,area] = demand[area]."],"objective":"Minimize sum_mine,area distance[mine,area] * shipment[mine,area] (ton-kilometers)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_lower = {
        "A": params["supply_A_lower"],
        "B": params["supply_B_lower"],
    }
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
    }
    distance = {
        ("A", 1): params["dist_A1"],
        ("A", 2): params["dist_A2"],
        ("A", 3): params["dist_A3"],
        ("B", 1): params["dist_B1"],
        ("B", 2): params["dist_B2"],
        ("B", 3): params["dist_B3"],
    }

    model = pyo.ConcreteModel()
    model.mines = pyo.Set(initialize=["A", "B"])
    model.areas = pyo.Set(initialize=[1, 2, 3])

    model.supply_lower = pyo.Param(
        model.mines, initialize=supply_lower
    )
    model.demand = pyo.Param(
        model.areas, initialize=demand
    )
    model.distance = pyo.Param(
        model.mines, model.areas, initialize=distance
    )

    model.shipment = pyo.Var(
        model.mines, model.areas, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, mine):
        return (
            sum(instance.shipment[mine, area] for area in instance.areas)
            >= instance.supply_lower[mine]
        )

    model.minimum_supply = pyo.Constraint(
        model.mines, rule=supply_rule
    )

    def demand_rule(instance, area):
        return (
            sum(instance.shipment[mine, area] for mine in instance.mines)
            == instance.demand[area]
        )

    model.demand_balance = pyo.Constraint(
        model.areas, rule=demand_rule
    )

    model.transport_objective = pyo.Objective(
        expr=sum(
            model.distance[mine, area] * model.shipment[mine, area]
            for mine in model.mines
            for area in model.areas
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.transport_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}