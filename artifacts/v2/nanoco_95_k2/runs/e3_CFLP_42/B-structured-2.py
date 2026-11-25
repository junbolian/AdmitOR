# IR: {"sets":{"I":"1..20","J":"1..5"},"params":{"opening_cost":"params['opening_cost'][j-1] for j in J","capacity":"params['capacity'][j-1] for j in J","demand":"params['demand'][i-1] for i in I","transport_cost":"params['transport_cost'][i-1][j-1] for i in I, j in J"},"variables":{"open_center[j]":"binary, j in J","assign[i,j]":"binary, i in I, j in J"},"constraints":["sum(assign[i,j] for j in J) == 1 for each i in I","sum(demand[i]*assign[i,j] for i in I) <= capacity[j]*open_center[j] for each j in J","assign[i,j] <= open_center[j] for each i in I, j in J"],"objective":"minimize sum(opening_cost[j]*open_center[j] for j in J) + sum(demand[i]*transport_cost[i,j]*assign[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences for vectors and the cost matrix."""
    model = pyo.ConcreteModel()

    model.hospitals = pyo.RangeSet(1, 20)
    model.centers = pyo.RangeSet(1, 5)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, j: params["opening_cost"][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, j: params["capacity"][j - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.hospitals,
        initialize=lambda mdl, i: params["demand"][i - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.hospitals,
        model.centers,
        initialize=lambda mdl, i, j: params["transport_cost"][i - 1][j - 1],
        within=pyo.NonNegativeReals,
    )

    model.open_center = pyo.Var(model.centers, domain=pyo.Binary)
    model.assign = pyo.Var(
        model.hospitals, model.centers, domain=pyo.Binary
    )

    def single_source_rule(mdl, i):
        return sum(mdl.assign[i, j] for j in mdl.centers) == 1

    model.single_source = pyo.Constraint(
        model.hospitals, rule=single_source_rule
    )

    def capacity_rule(mdl, j):
        return (
            sum(
                mdl.demand[i] * mdl.assign[i, j]
                for i in mdl.hospitals
            )
            <= mdl.capacity[j] * mdl.open_center[j]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    def opening_link_rule(mdl, i, j):
        return mdl.assign[i, j] <= mdl.open_center[j]

    model.opening_link = pyo.Constraint(
        model.hospitals, model.centers, rule=opening_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[j] * model.open_center[j]
            for j in model.centers
        )
        + sum(
            model.demand[i]
            * model.transport_cost[i, j]
            * model.assign[i, j]
            for i in model.hospitals
            for j in model.centers
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}