# IR: {"sets":{"items":"0..44"},"params":{"resource_limit":"params['resource_limit']","profit":"optional params['profit'] mapping or length-45 sequence, overriding known profits","resource_use":"optional params['resource_use'] mapping or length-45 sequence, overriding known resource coefficients","capacity":"optional params['capacity'] mapping or length-45 sequence, overriding known capacities"},"known_data":{"profit":{"0":381,"1":336,"2":352,"44":381},"resource_use":{"0":0.012048,"1":0.012821,"44":0.012821},"capacity":{"0":716,"1":606,"2":635,"44":618}},"variables":{"production[i]":"continuous nonnegative; upper bound capacity[i]"},"constraints":["sum(resource_use[i]*production[i] for i in items) <= resource_limit"],"objective":"maximize sum(profit[i]*production[i] for i in items)","failure_policy":"Return missing_item_data if coefficients remain unspecified; otherwise solve with Highs and determine success solely by objective retrieval."}

# The supplied statement does not specify all 135 item coefficients.
# Consequently, no script can compute its exact optimum from resource_limit
# alone without inventing data. To make this formulation solvable, supply
# the omitted coefficients through params["profit"], params["resource_use"],
# and params["capacity"]. Each may be an integer-keyed mapping or a
# length-45 sequence. Supplied entries override the known examples.
# With only resource_limit, missing_item_data remains unavoidable.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _merge_coefficients(params, key, known):
    coefficients = dict(known)

    if key not in params:
        return coefficients

    supplied = params[key]
    if hasattr(supplied, "items"):
        coefficients.update(supplied)
    else:
        if len(supplied) != 45:
            raise ValueError(f"params[{key!r}] must contain 45 entries.")
        coefficients.update(enumerate(supplied))

    return coefficients


def solve(params):
    resource_limit = params["resource_limit"]
    items = range(45)

    profit = _merge_coefficients(
        params,
        "profit",
        {0: 381, 1: 336, 2: 352, 44: 381},
    )
    resource_use = _merge_coefficients(
        params,
        "resource_use",
        {0: 0.012048, 1: 0.012821, 44: 0.012821},
    )
    capacity = _merge_coefficients(
        params,
        "capacity",
        {0: 716, 1: 606, 2: 635, 44: 618},
    )

    if any(
        item not in coefficients or coefficients[item] is None
        for coefficients in (profit, resource_use, capacity)
        for item in items
    ):
        return {"objective": None, "status": "missing_item_data"}

    model = pyo.ConcreteModel()
    model.items = pyo.RangeSet(0, 44)

    model.resource_limit = pyo.Param(initialize=resource_limit)
    model.unit_profit = pyo.Param(
        model.items,
        initialize={item: profit[item] for item in items},
    )
    model.unit_resource = pyo.Param(
        model.items,
        initialize={item: resource_use[item] for item in items},
    )
    model.production_capacity = pyo.Param(
        model.items,
        initialize={item: capacity[item] for item in items},
    )

    def production_bounds(instance, item):
        return 0, instance.production_capacity[item]

    model.production = pyo.Var(
        model.items,
        domain=pyo.NonNegativeReals,
        bounds=production_bounds,
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(
            model.unit_resource[item] * model.production[item]
            for item in model.items
        )
        <= model.resource_limit
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[item] * model.production[item]
            for item in model.items
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi can raise this while attempting to load an absent solution.
        # Unexpected solver errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}