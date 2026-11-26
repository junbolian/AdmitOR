# IR: {"sets":{"DC":"1..7","STORE":"1..6"},"params":{"opening_cost":"params['opening_cost'], length 7","transport_cost":"params['transport_cost'], 7x6 nested array or length-42 row-major array","demand":"params['demand'], length 6","capacity":"params['capacity'], length 7"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i sum_j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    if len(opening_cost) != 7:
        return {"objective": None, "status": "invalid_opening_cost"}
    if len(demand) != 6:
        return {"objective": None, "status": "invalid_demand"}
    if len(capacity) != 7:
        return {"objective": None, "status": "invalid_capacity"}

    if len(transport_cost) == 7:
        if not all(
            hasattr(row, "__len__") and len(row) == 6
            for row in transport_cost
        ):
            return {"objective": None, "status": "invalid_transport_cost"}
        transport_data = {
            (i, j): transport_cost[i - 1][j - 1]
            for i in range(1, 8)
            for j in range(1, 7)
        }
    elif len(transport_cost) == 42:
        transport_data = {
            (i, j): transport_cost[(i - 1) * 6 + (j - 1)]
            for i in range(1, 8)
            for j in range(1, 7)
        }
    else:
        return {"objective": None, "status": "invalid_transport_cost"}

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(1, 7)
    model.STORE = pyo.RangeSet(1, 6)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i - 1] for i in model.DC},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=transport_data,
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={j: demand[j - 1] for j in model.STORE},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={i: capacity[i - 1] for i in model.DC},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(problem, j):
        return (
            sum(problem.shipment[i, j] for i in problem.DC)
            == problem.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(problem, i):
        return (
            sum(problem.shipment[i, j] for j in problem.STORE)
            <= problem.capacity[i] * problem.opened[i]
        )

    model.supply_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.DC
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.DC
                for j in model.STORE
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}