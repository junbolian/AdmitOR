# IR: {"sets":{"origins":[0,1,2,3,4],"destinations":[0,1,2,3,4]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"flow[i,j]":"continuous, nonnegative"},"constraints":["sum_j flow[i,j] == supply[i] for each origin i","sum_i flow[i,j] == demand[j] for each destination j","flow[i,j] <= capacity[i,j] for each lane (i,j)"],"objective":"minimize sum_i sum_j cost[i,j] * flow[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-five vectors and five-by-five nested matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 4)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): capacity[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def supply_rule(network, i):
        return sum(
            network.flow[i, j] for j in network.destinations
        ) == network.supply[i]

    def demand_rule(network, j):
        return sum(
            network.flow[i, j] for i in network.origins
        ) == network.demand[j]

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.lane_limits = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}