# IR: {"sets":{"regions":[1,2,3,4,5],"links":[[1,3],[1,4],[1,5],[2,3],[2,4],[2,5],[3,4],[3,5],[4,5]],"arcs":"both directions of every link"},"params":{"cost":"cost_i_j for each listed link; equal in both directions","supply":"supply_1,...,supply_5","demand":"demand_1,...,demand_5"},"variables":{"flow[i,j]":"nonnegative continuous for every arc"},"constraints":["For each region r: supply[r] + sum(flow[i,r]) - sum(flow[r,j]) >= demand[r]."],"objective":"Minimize sum(cost[i,j] * flow[i,j]) over all arcs.","assumptions":["Each listed connection permits movement in either direction at the listed unit cost.","Surplus cars may remain in their regions."],"reporting":"Return the optimal objective rounded to the nearest dollar."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    regions = (1, 2, 3, 4, 5)

    link_costs = {
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }
    supply = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }
    demand = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }

    arc_costs = {}
    for (origin, destination), unit_cost in link_costs.items():
        arc_costs[origin, destination] = unit_cost
        arc_costs[destination, origin] = unit_cost

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=tuple(arc_costs), ordered=True
    )

    model.move_cost = pyo.Param(model.arcs, initialize=arc_costs)
    model.initial_supply = pyo.Param(model.regions, initialize=supply)
    model.required_cars = pyo.Param(model.regions, initialize=demand)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def meet_demand_rule(instance, region):
        incoming = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if destination == region
        )
        outgoing = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if origin == region
        )
        return (
            instance.initial_supply[region] + incoming - outgoing
            >= instance.required_cars[region]
        )

    model.meet_demand = pyo.Constraint(
        model.regions, rule=meet_demand_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.move_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
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

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}