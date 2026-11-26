# IR: {"sets":{"cities":[0,1,2,3,4,5],"arcs":[[0,1],[0,2],[0,3],[0,5],[1,0],[1,2],[1,3],[1,4],[1,5],[2,0],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,4],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"params['capacity_{i}_{j}'] for each arc (i,j)"},"variables":{"flow[i,j]":"NonNegativeReals for each arc","throughput":"NonNegativeReals"},"constraints":["flow[i,j] <= capacity[i,j] for each arc","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=5, otherwise 0, for each city i"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (0, 1, 2, 3, 4, 5)
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 0), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    )

    capacity_data = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        city: tuple(arc for arc in arcs if arc[0] == city)
        for city in cities
    }
    incoming = {
        city: tuple(arc for arc in arcs if arc[1] == city)
        for city in cities
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(instance, city):
        net_outflow = (
            sum(instance.flow[arc] for arc in outgoing[city])
            - sum(instance.flow[arc] for arc in incoming[city])
        )
        if city == 0:
            return net_outflow == instance.throughput
        if city == 5:
            return net_outflow == -instance.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)
    model.objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}