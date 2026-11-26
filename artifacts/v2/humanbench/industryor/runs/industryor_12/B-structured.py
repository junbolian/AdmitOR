# IR: {"sets":{"P":["A","B","C"],"R":["tech_prep","labor","material"],"K":{"A":[1,2,3,4],"B":[1,2,3],"C":[1,2]}},"params":["tech_prep_A","tech_prep_B","tech_prep_C","labor_A","labor_B","labor_C","material_A","material_B","material_C","capacity_tech_prep","capacity_labor","capacity_material","profit_A_tier1","profit_A_tier2","profit_A_tier3","profit_A_tier4","profit_B_tier1","profit_B_tier2","profit_B_tier3","profit_C_tier1","profit_C_tier2","breakpoint_A_1","breakpoint_A_2","breakpoint_A_3","breakpoint_B_1","breakpoint_B_2","breakpoint_C_1"],"interpretation":"Continuous production; profit rates apply incrementally to successive sales tiers.","derived":{"width[p,k]":"breakpoint[p,k]-breakpoint[p,k-1], with breakpoint[p,0]=0, for finite tiers","U[p]":"min(capacity[r]/requirement[r,p] for r in R); requirements must be positive"},"variables":{"x[p,k]":"NonNegativeReals: units sold in tier k","y[p,k]":"Binary, k>=2: tier k is enabled"},"constraints":["For each resource r: sum(requirement[r,p]*x[p,k] for p,k)<=capacity[r].","For each product p: x[p,1]<=width[p,1].","For each nonfinal tier k>=2: x[p,k]<=width[p,k]*y[p,k].","For each final tier k: x[p,k]<=U[p]*y[p,k].","For each tier k>=2: x[p,k-1]>=width[p,k-1]*y[p,k]."],"objective":"maximize sum(profit[p,k]*x[p,k] for p,k)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ("A", "B", "C")
    resources = ("tech_prep", "labor", "material")
    tier_counts = {"A": 4, "B": 3, "C": 2}

    requirements = {
        ("tech_prep", "A"): params["tech_prep_A"],
        ("tech_prep", "B"): params["tech_prep_B"],
        ("tech_prep", "C"): params["tech_prep_C"],
        ("labor", "A"): params["labor_A"],
        ("labor", "B"): params["labor_B"],
        ("labor", "C"): params["labor_C"],
        ("material", "A"): params["material_A"],
        ("material", "B"): params["material_B"],
        ("material", "C"): params["material_C"],
    }

    capacities = {
        "tech_prep": params["capacity_tech_prep"],
        "labor": params["capacity_labor"],
        "material": params["capacity_material"],
    }

    profits = {
        ("A", 1): params["profit_A_tier1"],
        ("A", 2): params["profit_A_tier2"],
        ("A", 3): params["profit_A_tier3"],
        ("A", 4): params["profit_A_tier4"],
        ("B", 1): params["profit_B_tier1"],
        ("B", 2): params["profit_B_tier2"],
        ("B", 3): params["profit_B_tier3"],
        ("C", 1): params["profit_C_tier1"],
        ("C", 2): params["profit_C_tier2"],
    }

    breakpoints = {
        "A": (
            params["breakpoint_A_1"],
            params["breakpoint_A_2"],
            params["breakpoint_A_3"],
        ),
        "B": (
            params["breakpoint_B_1"],
            params["breakpoint_B_2"],
        ),
        "C": (params["breakpoint_C_1"],),
    }

    if any(value <= 0 for value in requirements.values()):
        raise ValueError("Resource requirements must be positive.")

    for product in products:
        previous = 0
        for breakpoint in breakpoints[product]:
            if breakpoint < previous:
                raise ValueError(
                    "Breakpoints must be nonnegative and nondecreasing."
                )
            previous = breakpoint

    widths = {}
    for product in products:
        previous = 0
        for tier, breakpoint in enumerate(breakpoints[product], start=1):
            widths[product, tier] = breakpoint - previous
            previous = breakpoint

    upper_bounds = {
        product: min(
            capacities[resource] / requirements[resource, product]
            for resource in resources
        )
        for product in products
    }

    tier_pairs = [
        (product, tier)
        for product in products
        for tier in range(1, tier_counts[product] + 1)
    ]
    later_tier_pairs = [
        (product, tier)
        for product, tier in tier_pairs
        if tier >= 2
    ]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.resources = pyo.Set(initialize=resources, ordered=True)
    model.tier_pairs = pyo.Set(
        dimen=2, initialize=tier_pairs, ordered=True
    )
    model.later_tier_pairs = pyo.Set(
        dimen=2, initialize=later_tier_pairs, ordered=True
    )

    model.x = pyo.Var(model.tier_pairs, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.later_tier_pairs, domain=pyo.Binary)

    def resource_capacity_rule(instance, resource):
        return sum(
            requirements[resource, product] * instance.x[product, tier]
            for product, tier in tier_pairs
        ) <= capacities[resource]

    model.resource_limits = pyo.Constraint(
        model.resources, rule=resource_capacity_rule
    )

    def first_tier_rule(instance, product):
        return instance.x[product, 1] <= widths[product, 1]

    model.first_tier_limits = pyo.Constraint(
        model.products, rule=first_tier_rule
    )

    def later_tier_limit_rule(instance, product, tier):
        limit = (
            upper_bounds[product]
            if tier == tier_counts[product]
            else widths[product, tier]
        )
        return instance.x[product, tier] <= limit * instance.y[product, tier]

    model.later_tier_limits = pyo.Constraint(
        model.later_tier_pairs, rule=later_tier_limit_rule
    )

    def tier_sequence_rule(instance, product, tier):
        return (
            instance.x[product, tier - 1]
            >= widths[product, tier - 1] * instance.y[product, tier]
        )

    model.tier_sequence = pyo.Constraint(
        model.later_tier_pairs, rule=tier_sequence_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profits[product, tier] * model.x[product, tier]
            for product, tier in tier_pairs
        ),
        sense=pyo.maximize,
    )

    # An unsuccessful solve may raise before any solution is loaded.
    # Success is determined exclusively by objective-value retrieval.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}