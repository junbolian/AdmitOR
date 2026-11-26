# IR: {"sets":{"C":"range(params['num_cities'])","A":"[(i,j) for i in C for j in C if i!=j], row-major"},"params":{"num_cities":"params['num_cities']","supply_demand":"params['supply_demand'][i]; positive=supply, negative=demand","cost_matrix":"params['cost_matrix']; accept flat off-diagonal, flat full matrix, or nested rows with or without diagonals; map to A","capacity_matrix":"params['capacity_matrix']; same formats and mapping as cost_matrix"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":{"city_balance[i]":"sum(flow[i,j] for j!=i)-sum(flow[j,i] for j!=i)=supply_demand[i]","route_capacity[i,j]":"flow[i,j]<=capacity_matrix[i,j]"},"objective":"minimize sum(cost_matrix[i,j]*flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _normalize_routes(values, num_cities, arcs):
    """Normalize full or off-diagonal, flat or nested matrix data."""
    entries = list(values)

    if len(entries) == num_cities:
        try:
            rows = [list(row) for row in entries]
        except TypeError:
            rows = None

        if rows is not None:
            if all(len(row) == num_cities for row in rows):
                return {(i, j): rows[i][j] for i, j in arcs}

            if all(len(row) == num_cities - 1 for row in rows):
                result = {}
                for i in range(num_cities):
                    position = 0
                    for j in range(num_cities):
                        if i != j:
                            result[i, j] = rows[i][position]
                            position += 1
                return result

            return None

    if len(entries) == len(arcs):
        return dict(zip(arcs, entries))

    if len(entries) == num_cities * num_cities:
        return {
            (i, j): entries[i * num_cities + j]
            for i, j in arcs
        }

    return None


def solve(params):
    num_cities = params["num_cities"]
    supply_demand = list(params["supply_demand"])
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    cities = list(range(num_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    if len(supply_demand) != num_cities:
        return {"objective": None, "status": "invalid_supply_dimensions"}

    route_costs = _normalize_routes(cost_matrix, num_cities, arcs)
    if route_costs is None:
        return {"objective": None, "status": "invalid_cost_dimensions"}

    route_capacities = _normalize_routes(capacity_matrix, num_cities, arcs)
    if route_capacities is None:
        return {"objective": None, "status": "invalid_capacity_dimensions"}

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
    model.route_limit = pyo.Param(
        model.arcs,
        initialize=route_capacities,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(instance, i):
        outgoing = pyo.quicksum(
            instance.flow[i, j] for j in instance.cities if j != i
        )
        incoming = pyo.quicksum(
            instance.flow[j, i] for j in instance.cities if j != i
        )
        return outgoing - incoming == instance.net_supply[i]

    model.city_balance = pyo.Constraint(
        model.cities,
        rule=balance_rule,
    )

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.route_limit[i, j]

    model.route_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.route_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}