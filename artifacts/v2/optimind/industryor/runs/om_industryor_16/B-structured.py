# IR: {"sets":{"fabrics":["curtain","clothing"],"priorities":[1,2,3,4]},"params":{"production_rate":"positive","regular_time":"nonnegative","overtime_limit":"nonnegative","curtain_demand":"nonnegative","curtain_profit":"real, informational","clothing_demand":"nonnegative","clothing_profit":"real, informational"},"variables":{"production[fabrics]":"nonnegative continuous","sales_shortfall[fabrics]":"nonnegative continuous","regular_shortfall":"nonnegative continuous","overtime":"nonnegative continuous","overtime_excess":"nonnegative continuous"},"constraints":["production[f] <= demand[f]","production[f] + sales_shortfall[f] = demand[f]","sum(production[f])/production_rate + regular_shortfall - overtime = regular_time","regular_shortfall <= regular_time","overtime <= overtime_limit + overtime_excess","after each priority except the last, fix its expression to its attained optimum"],"objective":"lexicographically minimize (regular_shortfall, overtime_excess, sum(sales_shortfall[f]), overtime); return the final-priority objective"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Full utilization means avoiding unused regular hours. Overtime is
    # permitted, with violations of its allowable limit penalized at priority 2.
    # Demand values are hard sales caps and priority-3 sales targets.
    # Profits are retained as data: the stated priorities contain no profit goal.
    model = pyo.ConcreteModel()

    model.fabrics = pyo.Set(
        initialize=("curtain", "clothing"),
        ordered=True,
    )

    model.production_rate = pyo.Param(
        initialize=params["production_rate"],
        within=pyo.PositiveReals,
    )
    model.regular_time = pyo.Param(
        initialize=params["regular_time"],
        within=pyo.NonNegativeReals,
    )
    model.overtime_limit = pyo.Param(
        initialize=params["overtime_limit"],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.fabrics,
        initialize={
            "curtain": params["curtain_demand"],
            "clothing": params["clothing_demand"],
        },
        within=pyo.NonNegativeReals,
    )
    model.profit = pyo.Param(
        model.fabrics,
        initialize={
            "curtain": params["curtain_profit"],
            "clothing": params["clothing_profit"],
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.fabrics,
        domain=pyo.NonNegativeReals,
    )
    model.sales_shortfall = pyo.Var(
        model.fabrics,
        domain=pyo.NonNegativeReals,
    )
    model.regular_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_excess = pyo.Var(domain=pyo.NonNegativeReals)

    def sales_cap_rule(instance, fabric):
        return instance.production[fabric] <= instance.demand[fabric]

    model.sales_caps = pyo.Constraint(
        model.fabrics,
        rule=sales_cap_rule,
    )

    def sales_target_rule(instance, fabric):
        return (
            instance.production[fabric] + instance.sales_shortfall[fabric]
            == instance.demand[fabric]
        )

    model.sales_targets = pyo.Constraint(
        model.fabrics,
        rule=sales_target_rule,
    )

    model.time_balance = pyo.Constraint(
        expr=(
            sum(model.production[fabric] for fabric in model.fabrics)
            / model.production_rate
            + model.regular_shortfall
            - model.overtime
            == model.regular_time
        )
    )
    model.regular_shortfall_bound = pyo.Constraint(
        expr=model.regular_shortfall <= model.regular_time
    )
    model.overtime_allowance = pyo.Constraint(
        expr=model.overtime <= model.overtime_limit + model.overtime_excess
    )

    priority_expressions = (
        model.regular_shortfall,
        model.overtime_excess,
        sum(model.sales_shortfall[fabric] for fabric in model.fabrics),
        model.overtime,
    )

    model.priority_locks = pyo.ConstraintList()
    model.priority_objective = pyo.Objective(
        expr=priority_expressions[0],
        sense=pyo.minimize,
    )

    # Sequential optimization enforces strict priorities without large weights.
    for priority_index, expression in enumerate(priority_expressions):
        model.priority_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            # APPsi raises when a feasible solution cannot be loaded.
            return {"objective": None, "status": "solve_failed"}

        try:
            obj_val = float(pyo.value(model.priority_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.priority_locks.add(expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}