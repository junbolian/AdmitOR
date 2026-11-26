# IR: {"sets":{"P":[0,1,2],"product_order":["A1","A2","A3"]},"params":{"days":"scalar","max_demand":"vector[P]","price":"vector[P]","prod_cost":"vector[P]","quota":"positive vector[P]","activation_cost":"vector[P]","min_batch":"vector[P]"},"variables":{"quantity[P]":"continuous nonnegative, units of 100 kg","line_on[P]":"binary"},"constraints":["sum(quantity[i]/quota[i] for i in P) <= days","quantity[i] <= max_demand[i]*line_on[i] for i in P","quantity[i] >= min_batch[i]*line_on[i] for i in P"],"objective":"maximize sum((price[i]-prod_cost[i])*quantity[i]-activation_cost[i]*line_on[i] for i in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Vector parameters use indices 0, 1, 2 for A1, A2, A3."""
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)

    model.days = pyo.Param(
        initialize=params["days"], within=pyo.NonNegativeReals
    )
    model.max_demand = pyo.Param(
        model.products,
        initialize={i: params["max_demand"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.price = pyo.Param(
        model.products,
        initialize={i: params["price"][i] for i in model.products},
        within=pyo.Reals,
    )
    model.prod_cost = pyo.Param(
        model.products,
        initialize={i: params["prod_cost"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.quota = pyo.Param(
        model.products,
        initialize={i: params["quota"][i] for i in model.products},
        within=pyo.PositiveReals,
    )
    model.activation_cost = pyo.Param(
        model.products,
        initialize={i: params["activation_cost"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )
    model.min_batch = pyo.Param(
        model.products,
        initialize={i: params["min_batch"][i] for i in model.products},
        within=pyo.NonNegativeReals,
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.line_on = pyo.Var(model.products, domain=pyo.Binary)

    # Each production quantity consumes quantity/quota days of shared capacity.
    model.calendar_capacity = pyo.Constraint(
        expr=sum(
            model.quantity[i] / model.quota[i] for i in model.products
        ) <= model.days
    )

    def demand_activation_rule(block, i):
        return (
            block.quantity[i]
            <= block.max_demand[i] * block.line_on[i]
        )

    model.demand_activation = pyo.Constraint(
        model.products, rule=demand_activation_rule
    )

    def minimum_batch_rule(block, i):
        return block.quantity[i] >= block.min_batch[i] * block.line_on[i]

    model.minimum_batch = pyo.Constraint(
        model.products, rule=minimum_batch_rule
    )

    # Net revenue accounts for variable production and fixed activation costs.
    model.net_revenue = pyo.Objective(
        expr=sum(
            (model.price[i] - model.prod_cost[i]) * model.quantity[i]
            - model.activation_cost[i] * model.line_on[i]
            for i in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.net_revenue))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}