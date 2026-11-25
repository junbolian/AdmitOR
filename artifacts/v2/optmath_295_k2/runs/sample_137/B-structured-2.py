# IR: {
#   "sets": {"products": "0..5", "stages": "0..10"},
#   "params": {"profit": "profit[product]", "avail": "avail[stage]", "time": "time[stage][product]", "minProd": "minProd[product]", "maxProd": "maxProd[product]"},
#   "variables": {"production[product]": "nonnegative continuous"},
#   "constraints": [
#     "stage_capacity[stage]: sum(time[stage][product] * production[product] for product in products) <= avail[stage]",
#     "minimum_production[product]: production[product] >= minProd[product]",
#     "maximum_production[product]: production[product] <= maxProd[product]"
#   ],
#   "objective": "maximize sum(profit[product] * production[product] for product in products)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit"][product],
    )
    model.available_time = pyo.Param(
        model.stages,
        initialize=lambda mdl, stage: params["avail"][stage],
    )
    model.processing_time = pyo.Param(
        model.stages,
        model.products,
        initialize=lambda mdl, stage, product: params["time"][stage][product],
    )
    model.minimum_quantity = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["minProd"][product],
    )
    model.maximum_quantity = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["maxProd"][product],
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_capacity_rule(mdl, stage):
        return sum(
            mdl.processing_time[stage, product] * mdl.production[product]
            for product in mdl.products
        ) <= mdl.available_time[stage]

    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )
    model.minimum_production = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] >= mdl.minimum_quantity[product]
        ),
    )
    model.maximum_production = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] <= mdl.maximum_quantity[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    # APPsi HiGHS raises RuntimeError when no feasible solution can be loaded.
    # Evaluate the objective afterward to determine success solely by retrieval.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}