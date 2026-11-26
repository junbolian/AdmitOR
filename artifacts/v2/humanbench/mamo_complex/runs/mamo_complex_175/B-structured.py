# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j} minus {(1,5),(2,1)}"},"params":{"capacity[i,j]":"params['capacity_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=7, else 0, for every i in N"],"objective":"maximize throughput"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
        and (origin, destination) not in {(1, 5), (2, 1)}
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        node: tuple(destination for origin, destination in arcs if origin == node)
        for node in nodes
    }
    incoming = {
        node: tuple(origin for origin, destination in arcs if destination == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(
                network.flow[node, destination]
                for destination in outgoing[node]
            )
            - pyo.quicksum(
                network.flow[origin, node]
                for origin in incoming[node]
            )
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 7:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.max_flow = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.max_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}