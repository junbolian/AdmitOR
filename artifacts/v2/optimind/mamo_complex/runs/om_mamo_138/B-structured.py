# IR: {"sets":{"V":[0,1,2,3,4,5],"A":[[0,1],[0,2],[0,4],[0,5],[1,0],[1,2],[1,3],[1,4],[1,5],[2,0],[2,1],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,4],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"corresponding params['cap_i_j'], in thousands of vehicles/hour"},"variables":{"flow[i,j]":"continuous nonnegative, indexed by A","throughput":"continuous nonnegative, thousands of vehicles/hour"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","outflow[v] - inflow[v] = throughput if v=0, -throughput if v=5, and 0 otherwise, for every v in V"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        (0, 1): params["cap_0_1"],
        (0, 2): params["cap_0_2"],
        (0, 4): params["cap_0_4"],
        (0, 5): params["cap_0_5"],
        (1, 0): params["cap_1_0"],
        (1, 2): params["cap_1_2"],
        (1, 3): params["cap_1_3"],
        (1, 4): params["cap_1_4"],
        (1, 5): params["cap_1_5"],
        (2, 0): params["cap_2_0"],
        (2, 1): params["cap_2_1"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (2, 5): params["cap_2_5"],
        (3, 0): params["cap_3_0"],
        (3, 1): params["cap_3_1"],
        (3, 2): params["cap_3_2"],
        (3, 4): params["cap_3_4"],
        (3, 5): params["cap_3_5"],
        (4, 0): params["cap_4_0"],
        (4, 1): params["cap_4_1"],
        (4, 2): params["cap_4_2"],
        (4, 3): params["cap_4_3"],
        (4, 5): params["cap_4_5"],
        (5, 0): params["cap_5_0"],
        (5, 1): params["cap_5_1"],
        (5, 2): params["cap_5_2"],
        (5, 3): params["cap_5_3"],
        (5, 4): params["cap_5_4"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=capacities.keys(), ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
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
        outflow = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if origin == city
        )
        inflow = sum(
            instance.flow[origin, destination]
            for origin, destination in instance.arcs
            if destination == city
        )

        if city == 0:
            return outflow - inflow == instance.throughput
        if city == 5:
            return outflow - inflow == -instance.throughput
        return outflow - inflow == 0

    model.flow_balances = pyo.Constraint(
        model.cities, rule=balance_rule
    )
    model.max_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise before loading a solution.
        # Objective retrieval below is the sole success check.
        pass

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}