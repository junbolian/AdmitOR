# IR: {"sets":{"C":"range(num_cities)","A":"ordered pairs (i,j) in C x C with i != j, row-major"},"params":{"num_cities":"params['num_cities']","supply_demand":"params['supply_demand']; positive supply, negative demand","cost_matrix":"params['cost_matrix']; flat off-diagonal entries, n rows of n-1 entries, or n-by-n matrix with diagonal ignored","capacity_matrix":"params['capacity_matrix']; same supported layouts as cost_matrix"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["For each i in C: sum_j flow[i,j] - sum_j flow[j,i] = supply_demand[i], excluding j=i","For each (i,j) in A: flow[i,j] <= capacity_matrix[i,j]"],"objective":"minimize sum_(i,j in A) cost_matrix[i,j] * flow[i,j]"}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _arc_values(data, num_cities, arcs):
    """Normalize flat or row-based route data to an arc-indexed dictionary."""
    entries = list(data)

    if len(entries) == num_cities and all(
        hasattr(entry, "__iter__") for entry in entries
    ):
        rows = [list(row) for row in entries]

        if all(len(row) == num_cities for row in rows):
            return {(i, j): rows[i][j] for i, j in arcs}

        if all(len(row) == num_cities - 1 for row in rows):
            return {
                (i, j): rows[i][j if j < i else j - 1]
                for i, j in arcs
            }

        raise ValueError("Invalid route matrix dimensions.")

    if len(entries) != len(arcs):
        raise ValueError("Invalid number of route entries.")

    return {arc: entries[k] for k, arc in enumerate(arcs)}


def solve(params):
    num_cities = operator.index(params["num_cities"])
    supply_demand = list(params["supply_demand"])
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    if num_cities < 2 or len(supply_demand) != num_cities:
        return {"objective": None, "status": "invalid_dimensions"}

    cities = list(range(num_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    try:
        route_costs = _arc_values(cost_matrix, num_cities, arcs)
        route_capacities = _arc_values(capacity_matrix, num_cities, arcs)
    except ValueError:
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: supply_demand[i] for i in cities},
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.arcs,
        initialize=route_costs,
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.arcs,
        initialize=route_capacities,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(block, i):
        return (
            sum(block.flow[i, j] for j in block.cities if j != i)
            - sum(block.flow[j, i] for j in block.cities if j != i)
            == block.net_supply[i]
        )

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(block, i, j):
        return block.flow[i, j] <= block.route_capacity[i, j]

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
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