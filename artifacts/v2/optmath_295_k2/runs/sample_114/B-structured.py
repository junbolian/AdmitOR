# IR: {"sets":{"origins":"0..13","destinations":"0..13"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][14*i+j] (flat row-major), or params['cost'][i][j] (nested rows)"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] == supply[i] for each origin i","sum_i shipment[i,j] == demand[j] for each destination j"],"objective":"minimize sum_i sum_j cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]

    if len(supply_data) != 14 or len(demand_data) != 14:
        raise ValueError("Supply and demand must each contain 14 entries.")

    if len(cost_data) == 14 * 14:
        cost_values = {
            (i, j): cost_data[14 * i + j]
            for i in range(14)
            for j in range(14)
        }
    elif len(cost_data) == 14 and all(len(row) == 14 for row in cost_data):
        cost_values = {
            (i, j): cost_data[i][j]
            for i in range(14)
            for j in range(14)
        }
    else:
        raise ValueError("Cost must contain 196 row-major entries or 14 rows of 14 entries.")

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 13)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply_data[i] for i in range(14)},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand_data[j] for j in range(14)},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=cost_values,
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(problem, i):
        return sum(
            problem.shipment[i, j] for j in problem.destinations
        ) == problem.supply[i]

    def demand_rule(problem, j):
        return sum(
            problem.shipment[i, j] for i in problem.origins
        ) == problem.demand[j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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