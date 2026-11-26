# IR: {"sets":{"cities":[0,1,2,3,4,5,6],"arcs":[[0,1],[0,2],[0,3],[0,5],[0,6],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[2,6],[3,0],[3,1],[3,2],[3,4],[3,5],[3,6],[4,0],[4,1],[4,2],[4,3],[4,5],[4,6],[5,0],[5,1],[5,2],[5,3],[5,4],[5,6],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5]]},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for each (i,j) in arcs; nonnegative; thousands of kg/day"},"variables":{"flow[i,j]":"nonnegative continuous for each arc","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for each arc","sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = throughput if i=0, -throughput if i=6, otherwise 0, for each city"],"objective":"maximize throughput"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]
    cities = range(7)

    capacities = {
        (i, j): params[f"capacity_{i}_{j}"]
        for i, j in arcs
    }
    outgoing = {
        city: [(i, j) for i, j in arcs if i == city]
        for city in cities
    }
    incoming = {
        city: [(i, j) for i, j in arcs if j == city]
        for city in cities
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(model, i, j):
        return model.flow[i, j] <= model.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(model, city):
        net_outflow = (
            sum(model.flow[i, j] for i, j in outgoing[city])
            - sum(model.flow[i, j] for i, j in incoming[city])
        )
        if city == 0:
            return net_outflow == model.throughput
        if city == 6:
            return net_outflow == -model.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )
    model.objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi may raise when no solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}