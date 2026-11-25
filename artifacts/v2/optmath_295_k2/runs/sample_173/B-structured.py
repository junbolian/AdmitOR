# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"capacity":"capacity[i] from params","demand":"demand[j] from params","min_contributors":"scalar from params","min_delivery":"min_delivery[i] from params","cost":"cost[i][j] from params"},"variables":{"x[i,j]":"NonNegativeReals","y[i,j]":"Binary"},"constraints":["sum_j x[i,j] <= capacity[i] for each i","sum_i x[i,j] >= demand[j] for each j","sum_i y[i,j] >= min_contributors for each j","x[i,j] >= min_delivery[i]*y[i,j] for each i,j","x[i,j] <= capacity[i]*y[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed parameters as lists or integer-keyed mappings.

    The cost parameter must support nested indexing: params["cost"][i][j].
    The min_contributors parameter is a scalar.
    """
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 3)
    model.J = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.I,
        initialize={i: params["capacity"][i] for i in model.I},
    )
    model.demand = pyo.Param(
        model.J,
        initialize={j: params["demand"][j] for j in model.J},
    )
    model.min_contributors = pyo.Param(
        initialize=params["min_contributors"],
    )
    model.min_delivery = pyo.Param(
        model.I,
        initialize={i: params["min_delivery"][i] for i in model.I},
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, model.J, domain=pyo.Binary)

    def capacity_rule(block, i):
        return sum(block.x[i, j] for j in block.J) <= block.capacity[i]

    model.capacity_limit = pyo.Constraint(model.I, rule=capacity_rule)

    def demand_rule(block, j):
        return sum(block.x[i, j] for i in block.I) >= block.demand[j]

    model.demand_requirement = pyo.Constraint(model.J, rule=demand_rule)

    def contributors_rule(block, j):
        return (
            sum(block.y[i, j] for i in block.I)
            >= block.min_contributors
        )

    model.contributor_requirement = pyo.Constraint(
        model.J, rule=contributors_rule
    )

    def minimum_delivery_rule(block, i, j):
        return block.x[i, j] >= block.min_delivery[i] * block.y[i, j]

    model.delivery_lower_bound = pyo.Constraint(
        model.I, model.J, rule=minimum_delivery_rule
    )

    def delivery_link_rule(block, i, j):
        return block.x[i, j] <= block.capacity[i] * block.y[i, j]

    model.delivery_upper_bound = pyo.Constraint(
        model.I, model.J, rule=delivery_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Unexpected solver errors propagate to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}