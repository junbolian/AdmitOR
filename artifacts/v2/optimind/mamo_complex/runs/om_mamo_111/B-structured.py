# IR: {"sets":{"regions":[1,2,3,4,5],"pairs":"(i,j) with i<j","arcs":"(i,j) with i!=j"},"params":["cost_12","cost_13","cost_14","cost_15","cost_23","cost_24","cost_25","cost_34","cost_35","cost_45","supply_1","supply_2","supply_3","supply_4","supply_5","demand_1","demand_2","demand_3","demand_4","demand_5"],"derived":{"transport_cost[i,j]":"cost_ab where a=min(i,j), b=max(i,j); costs are symmetric"},"variables":{"flow[i,j]":{"type":"nonnegative continuous","indices":"arcs","meaning":"cars moved from region i to region j"}},"constraints":["For each region i: supply_i + sum(flow[j,i] for j!=i) - sum(flow[i,j] for j!=i) >= demand_i"],"objective":{"sense":"minimize","expression":"sum(transport_cost[i,j]*flow[i,j] for (i,j) in arcs)"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize relocation costs, allowing surplus cars to remain in any region."""
    regions = (1, 2, 3, 4, 5)
    arcs = [
        (origin, destination)
        for origin in regions
        for destination in regions
        if origin != destination
    ]

    pair_costs = {
        (1, 2): params["cost_12"],
        (1, 3): params["cost_13"],
        (1, 4): params["cost_14"],
        (1, 5): params["cost_15"],
        (2, 3): params["cost_23"],
        (2, 4): params["cost_24"],
        (2, 5): params["cost_25"],
        (3, 4): params["cost_34"],
        (3, 5): params["cost_35"],
        (4, 5): params["cost_45"],
    }
    supplies = {
        1: params["supply_1"],
        2: params["supply_2"],
        3: params["supply_3"],
        4: params["supply_4"],
        5: params["supply_5"],
    }
    demands = {
        1: params["demand_1"],
        2: params["demand_2"],
        3: params["demand_3"],
        4: params["demand_4"],
        5: params["demand_5"],
    }
    directed_costs = {
        (origin, destination): pair_costs[
            (min(origin, destination), max(origin, destination))
        ]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.Set(initialize=regions, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.transport_cost = pyo.Param(
        model.arcs, initialize=directed_costs, within=pyo.Reals
    )
    model.initial_supply = pyo.Param(
        model.regions, initialize=supplies, within=pyo.NonNegativeReals
    )
    model.required_cars = pyo.Param(
        model.regions, initialize=demands, within=pyo.NonNegativeReals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def regional_balance_rule(instance, region):
        incoming = sum(
            instance.flow[other, region]
            for other in instance.regions
            if other != region
        )
        outgoing = sum(
            instance.flow[region, other]
            for other in instance.regions
            if other != region
        )
        return (
            instance.initial_supply[region] + incoming - outgoing
            >= instance.required_cars[region]
        )

    model.regional_balance = pyo.Constraint(
        model.regions, rule=regional_balance_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}