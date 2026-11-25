# IR: {"sets":{"I":"0..44"},"params":{"resource_limit":"params['resource_limit']","profit":"45 fixed coefficients; only indices 0,1,2,44 supplied","resource":"45 fixed coefficients; only indices 0,1,44 supplied","capacity":"45 fixed coefficients; only indices 0,1,2,44 supplied"},"variables":{"production[i]":"NonNegativeReals"},"constraints":["production[i] <= capacity[i] for i in I","sum(resource[i]*production[i] for i in I) <= resource_limit"],"objective":"maximize sum(profit[i]*production[i] for i in I)","data_validation":"Return incomplete_problem_data if any required fixed coefficient is unknown."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


# The statement omits most of the 135 required item coefficients.
# The resource limit alone cannot determine the optimum. None explicitly
# represents missing data; replacing it with an invented number would solve
# a different problem. Complete these fixed tables with the omitted data.
# No additional keys in params are required.
ITEM_COUNT = 45

PROFIT = tuple(
    {0: 381, 1: 336, 2: 352, 44: 381}.get(item)
    for item in range(ITEM_COUNT)
)
RESOURCE = tuple(
    {0: 0.012048, 1: 0.012821, 44: 0.012821}.get(item)
    for item in range(ITEM_COUNT)
)
CAPACITY = tuple(
    {0: 716, 1: 606, 2: 635, 44: 618}.get(item)
    for item in range(ITEM_COUNT)
)


def solve(params):
    resource_limit = params["resource_limit"]

    # A complete numerical model cannot be built from the supplied statement.
    # This failure cannot be corrected without the missing coefficients.
    if any(
        coefficient is None
        for coefficients in (PROFIT, RESOURCE, CAPACITY)
        for coefficient in coefficients
    ):
        return {"objective": None, "status": "incomplete_problem_data"}

    model = pyo.ConcreteModel()
    model.items_set = pyo.RangeSet(0, ITEM_COUNT - 1)

    model.resource_budget = pyo.Param(initialize=resource_limit)
    model.unit_profit = pyo.Param(
        model.items_set,
        initialize=dict(enumerate(PROFIT)),
    )
    model.unit_resource = pyo.Param(
        model.items_set,
        initialize=dict(enumerate(RESOURCE)),
    )
    model.item_capacity = pyo.Param(
        model.items_set,
        initialize=dict(enumerate(CAPACITY)),
    )

    model.production = pyo.Var(
        model.items_set,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(instance, item):
        return instance.production[item] <= instance.item_capacity[item]

    model.capacity_constraints = pyo.Constraint(
        model.items_set,
        rule=capacity_rule,
    )
    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.unit_resource[item] * model.production[item]
            for item in model.items_set
        )
        <= model.resource_budget
    )
    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[item] * model.production[item]
            for item in model.items_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Determine success below solely through objective retrieval.

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}