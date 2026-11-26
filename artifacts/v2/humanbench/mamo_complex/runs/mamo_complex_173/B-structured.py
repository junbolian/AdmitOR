# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"directed arcs listed in outgoing"},"params":{"capacity[i,j]":"params['capacity_i_j'] for each (i,j) in A; nonnegative MW"},"variables":{"flow[i,j]":"continuous nonnegative for each (i,j) in A","throughput":"continuous nonnegative MW"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=6, and 0 otherwise, for every i in N"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    outgoing = {
        0: (1, 2, 3, 4, 5, 6),
        1: (0, 2, 3, 5, 6),
        2: (0, 1, 3, 4, 5, 6),
        3: (0, 2, 4, 5, 6),
        4: (0, 1, 2, 3, 5, 6),
        5: (0, 1, 2, 3, 4, 6),
        6: (0, 1, 2, 3, 4, 5),
    }
    arcs = [
        (tail, head)
        for tail, destinations in outgoing.items()
        for head in destinations
    ]
    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in range(7)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(grid, tail, head):
        return grid.flow[tail, head] <= grid.capacity[tail, head]

    model.line_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(grid, node):
        net_outflow = (
            sum(grid.flow[node, head] for head in outgoing[node])
            - sum(grid.flow[tail, node] for tail in incoming[node])
        )
        if node == 0:
            return net_outflow == grid.throughput
        if node == 6:
            return net_outflow == -grid.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.total_power = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_power))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}