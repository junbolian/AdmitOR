# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":"{(i,j): i,j in cities, i != j}"},"params":{"supply_0":"params['supply_0']","supply_1":"params['supply_1']","demand_2":"params['demand_2']","demand_3":"params['demand_3']","demand_4":"params['demand_4']","demand_5":"params['demand_5']","cost[i,j]":"params[f'cost_{i}_to_{j}'] for each arc","capacity[i,j]":"params[f'cap_{i}_to_{j}'] for each arc","net_supply":"{0:supply_0,1:supply_1,2:-demand_2,3:-demand_3,4:-demand_4,5:-demand_5}"},"variables":{"flow[i,j]":{"type":"NonNegativeReals","index":"arcs"}},"constraints":{"balance":"sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) == net_supply[i], for each city i","route_capacity":"flow[i,j] <= capacity[i,j], for each arc (i,j)"},"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for (i,j) in arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(6)
            for destination in range(6)
            if origin != destination
        ],
        ordered=True,
    )

    net_supply = {
        0: params["supply_0"],
        1: params["supply_1"],
        2: -params["demand_2"],
        3: -params["demand_3"],
        4: -params["demand_4"],
        5: -params["demand_5"],
    }

    model.net_supply = pyo.Param(
        model.cities, initialize=net_supply, within=pyo.Reals
    )
    model.transport_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_to_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cap_{origin}_to_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(problem, city):
        outgoing = sum(
            problem.flow[city, destination]
            for destination in problem.cities
            if destination != city
        )
        incoming = sum(
            problem.flow[origin, city]
            for origin in problem.cities
            if origin != city
        )
        return outgoing - incoming == problem.net_supply[city]

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(problem, origin, destination):
        return (
            problem.flow[origin, destination]
            <= problem.route_capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}