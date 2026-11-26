# IR: {"sets":{"products":["A","B","C"],"resources":["prep","labor","material"],"tiers":{"A":[0,1,2,3],"B":[0,1,2],"C":[0,1]}},"params":["prep_A","prep_B","prep_C","labor_A","labor_B","labor_C","material_A","material_B","material_C","tech_capacity","labor_capacity","material_capacity","profit_A_tiers","profit_B_tiers","profit_C_tiers","tier_breakpoints_A","tier_breakpoints_B","tier_breakpoints_C"],"interpretation":"Integer production quantities; the selected sales-volume tier determines per-unit profit on all units. Breakpoints belong to the lower-volume tier.","derived":{"L[p,0]":"0","L[p,t>0]":"floor(breakpoint[p,t-1])+1","U[p,t<last]":"min(floor(breakpoint[p,t]),production_bound[p])","production_bound[p]":"minimum floor(capacity[r]/usage[r,p]) over positive resource usages; if none, unbounded when final-tier profit is positive, otherwise floor(last_breakpoint[p])+1"},"variables":{"selected[p,t]":"Binary","quantity[p,t]":"NonNegativeIntegers"},"constraints":["sum_t selected[p,t] = 1 for each product p","quantity[p,t] >= L[p,t]*selected[p,t]","quantity[p,t] <= U[p,t]*selected[p,t], with U[p,last]=production_bound[p]","sum_(p,t) usage[r,p]*quantity[p,t] <= capacity[r] for each resource r"],"objective":"maximize sum_(p,t) profit[p,t]*quantity[p,t]"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B", "C")
    resources = ("prep", "labor", "material")

    usage = {
        ("prep", "A"): float(params["prep_A"]),
        ("prep", "B"): float(params["prep_B"]),
        ("prep", "C"): float(params["prep_C"]),
        ("labor", "A"): float(params["labor_A"]),
        ("labor", "B"): float(params["labor_B"]),
        ("labor", "C"): float(params["labor_C"]),
        ("material", "A"): float(params["material_A"]),
        ("material", "B"): float(params["material_B"]),
        ("material", "C"): float(params["material_C"]),
    }
    capacity = {
        "prep": float(params["tech_capacity"]),
        "labor": float(params["labor_capacity"]),
        "material": float(params["material_capacity"]),
    }
    profits = {
        "A": tuple(float(value) for value in params["profit_A_tiers"]),
        "B": tuple(float(value) for value in params["profit_B_tiers"]),
        "C": tuple(float(value) for value in params["profit_C_tiers"]),
    }
    breakpoints = {
        "A": tuple(float(value) for value in params["tier_breakpoints_A"]),
        "B": tuple(float(value) for value in params["tier_breakpoints_B"]),
        "C": tuple(float(value) for value in params["tier_breakpoints_C"]),
    }
    tier_counts = {"A": 4, "B": 3, "C": 2}

    numeric_values = (
        list(usage.values())
        + list(capacity.values())
        + [value for values in profits.values() for value in values]
        + [value for values in breakpoints.values() for value in values]
    )
    if not all(math.isfinite(value) for value in numeric_values):
        return {"objective": None, "status": "invalid_parameters"}

    if any(value < 0 for value in usage.values()):
        return {"objective": None, "status": "invalid_parameters"}

    for product in products:
        thresholds = breakpoints[product]
        if (
            len(profits[product]) != tier_counts[product]
            or len(thresholds) != tier_counts[product] - 1
            or any(value < 0 for value in thresholds)
            or any(
                thresholds[position] >= thresholds[position + 1]
                for position in range(len(thresholds) - 1)
            )
        ):
            return {"objective": None, "status": "invalid_parameters"}

    if any(value < 0 for value in capacity.values()):
        return {"objective": None, "status": "infeasible"}

    production_bounds = {}
    for product in products:
        resource_bounds = [
            math.floor(capacity[resource] / usage[resource, product])
            for resource in resources
            if usage[resource, product] > 0
        ]
        if resource_bounds:
            production_bounds[product] = min(resource_bounds)
        elif profits[product][-1] > 0:
            return {"objective": None, "status": "unbounded"}
        else:
            # With no resource consumption and nonpositive final-tier
            # profit, increasing quantity beyond this point cannot help.
            production_bounds[product] = (
                math.floor(breakpoints[product][-1]) + 1
            )

    tier_pairs = [
        (product, tier)
        for product in products
        for tier in range(tier_counts[product])
    ]

    lower_bounds = {}
    upper_bounds = {}
    for product, tier in tier_pairs:
        lower_bounds[product, tier] = (
            0
            if tier == 0
            else math.floor(breakpoints[product][tier - 1]) + 1
        )
        upper_bounds[product, tier] = (
            min(
                math.floor(breakpoints[product][tier]),
                production_bounds[product],
            )
            if tier < tier_counts[product] - 1
            else production_bounds[product]
        )

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.resources = pyo.Set(initialize=resources, ordered=True)
    model.tier_pairs = pyo.Set(
        dimen=2, initialize=tier_pairs, ordered=True
    )

    model.selected = pyo.Var(model.tier_pairs, domain=pyo.Binary)
    model.quantity = pyo.Var(
        model.tier_pairs, domain=pyo.NonNegativeIntegers
    )

    def tier_choice_rule(instance, product):
        return sum(
            instance.selected[product, tier]
            for tier in range(tier_counts[product])
        ) == 1

    model.tier_choice = pyo.Constraint(
        model.products, rule=tier_choice_rule
    )

    def tier_lower_rule(instance, product, tier):
        return instance.quantity[product, tier] >= (
            lower_bounds[product, tier]
            * instance.selected[product, tier]
        )

    model.tier_lower = pyo.Constraint(
        model.tier_pairs, rule=tier_lower_rule
    )

    def tier_upper_rule(instance, product, tier):
        return instance.quantity[product, tier] <= (
            upper_bounds[product, tier]
            * instance.selected[product, tier]
        )

    model.tier_upper = pyo.Constraint(
        model.tier_pairs, rule=tier_upper_rule
    )

    def resource_limit_rule(instance, resource):
        return sum(
            usage[resource, product] * instance.quantity[product, tier]
            for product, tier in instance.tier_pairs
        ) <= capacity[resource]

    model.resource_limit = pyo.Constraint(
        model.resources, rule=resource_limit_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profits[product][tier] * model.quantity[product, tier]
            for product, tier in model.tier_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}