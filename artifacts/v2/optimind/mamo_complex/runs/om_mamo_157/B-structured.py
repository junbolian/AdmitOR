# IR: {"sets":{"R":[1,2,3,4],"P":["regular","premium"]},"params":{"octane_rating":"R -> real","raw_availability":"R -> nonnegative real","raw_cost":"R -> real","min_octane_product":"P -> real","selling_price":"P -> real","max_demand":"P -> nonnegative real"},"variables":{"blend[r,p]":"nonnegative continuous barrels"},"constraints":["For each r: sum_p blend[r,p] <= raw_availability[r]","For each p: sum_r blend[r,p] <= max_demand[p]","For each p: sum_r (octane_rating[r]-min_octane_product[p])*blend[r,p] >= 0"],"objective":"maximize sum_{r,p} (selling_price[p]-raw_cost[r])*blend[r,p]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_values(data, labels):
    """Accept ordered sequences or mappings keyed by labels or numeric indices."""
    if not isinstance(data, Mapping):
        values = list(data)
        if len(values) != len(labels):
            raise ValueError("Parameter sequence has an incorrect length.")
        return dict(zip(labels, values))

    candidate_keys = (
        tuple(labels),
        tuple(str(label) for label in labels),
        tuple(range(len(labels))),
        tuple(str(position) for position in range(len(labels))),
        tuple(range(1, len(labels) + 1)),
        tuple(str(position) for position in range(1, len(labels) + 1)),
    )
    for keys in candidate_keys:
        if all(key in data for key in keys):
            return {label: data[key] for label, key in zip(labels, keys)}

    raise ValueError("Parameter mapping has missing or unsupported keys.")


def solve(params):
    """
    Maximize daily blending profit.

    Sequence inputs follow raw gasoline order 1-4 and product order
    regular, premium. Mappings may use these labels or numeric indices.
    Additives have no separately specified volume or cost parameter.
    """
    raw_types = (1, 2, 3, 4)
    products = ("regular", "premium")

    octane_rating = _indexed_values(params["octane_rating"], raw_types)
    raw_availability = _indexed_values(params["raw_availability"], raw_types)
    raw_cost = _indexed_values(params["raw_cost"], raw_types)
    min_octane_product = _indexed_values(params["min_octane_product"], products)
    selling_price = _indexed_values(params["selling_price"], products)
    max_demand = _indexed_values(params["max_demand"], products)

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=raw_types, ordered=True)
    model.P = pyo.Set(initialize=products, ordered=True)

    model.octane_rating = pyo.Param(
        model.R, initialize=octane_rating, within=pyo.Reals
    )
    model.raw_availability = pyo.Param(
        model.R, initialize=raw_availability, within=pyo.NonNegativeReals
    )
    model.raw_cost = pyo.Param(
        model.R, initialize=raw_cost, within=pyo.Reals
    )
    model.min_octane_product = pyo.Param(
        model.P, initialize=min_octane_product, within=pyo.Reals
    )
    model.selling_price = pyo.Param(
        model.P, initialize=selling_price, within=pyo.Reals
    )
    model.max_demand = pyo.Param(
        model.P, initialize=max_demand, within=pyo.NonNegativeReals
    )

    model.blend = pyo.Var(model.R, model.P, domain=pyo.NonNegativeReals)

    def raw_supply_rule(model, raw):
        return (
            sum(model.blend[raw, product] for product in model.P)
            <= model.raw_availability[raw]
        )

    model.raw_supply_limit = pyo.Constraint(model.R, rule=raw_supply_rule)

    def product_demand_rule(model, product):
        return (
            sum(model.blend[raw, product] for raw in model.R)
            <= model.max_demand[product]
        )

    model.product_demand_limit = pyo.Constraint(
        model.P, rule=product_demand_rule
    )

    def product_octane_rule(model, product):
        return sum(
            (
                model.octane_rating[raw]
                - model.min_octane_product[product]
            )
            * model.blend[raw, product]
            for raw in model.R
        ) >= 0

    model.product_octane_requirement = pyo.Constraint(
        model.P, rule=product_octane_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            (model.selling_price[product] - model.raw_cost[raw])
            * model.blend[raw, product]
            for raw in model.R
            for product in model.P
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}