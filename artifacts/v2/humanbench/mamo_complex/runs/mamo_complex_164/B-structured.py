# {
#   "sets": {"N": "range(num_cities)", "A": "(i,j) in N x N with i != j, excluding (0,1),(0,4),(5,7),(8,0)"},
#   "params": {"num_cities": "params['num_cities'] (fixed at 9)", "capacity[i,j]": "params[f'cap_{i}_{j}'] for every (i,j) in A"},
#   "variables": {"flow[i,j]": "continuous nonnegative for (i,j) in A", "flow_value": "continuous nonnegative"},
#   "constraints": ["flow[i,j] <= capacity[i,j] for every (i,j) in A", "outflow[v] - inflow[v] = flow_value if v=0, -flow_value if v=num_cities-1, otherwise 0, for every v in N"],
#   "objective": "maximize flow_value"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    nodes = tuple(range(num_cities))
    excluded_arcs = {(0, 1), (0, 4), (5, 7), (8, 0)}
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination
        and (origin, destination) not in excluded_arcs
    )
    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }

    outgoing = {
        city: tuple(arc for arc in arcs if arc[0] == city)
        for city in nodes
    }
    incoming = {
        city: tuple(arc for arc in arcs if arc[1] == city)
        for city in nodes
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=nodes, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.routes,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)
    model.flow_value = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(block, origin, destination):
        return (
            block.flow[origin, destination]
            <= block.capacity[origin, destination]
        )

    model.route_limits = pyo.Constraint(
        model.routes,
        rule=capacity_rule,
    )

    def balance_rule(block, city):
        net_outflow = (
            pyo.quicksum(block.flow[arc] for arc in outgoing[city])
            - pyo.quicksum(block.flow[arc] for arc in incoming[city])
        )
        if city == 0:
            return net_outflow == block.flow_value
        if city == num_cities - 1:
            return net_outflow == -block.flow_value
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.cities,
        rule=balance_rule,
    )
    model.total_flow = pyo.Objective(
        expr=model.flow_value,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions still propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}