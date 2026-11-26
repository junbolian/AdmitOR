# IR: {"sets":{"fabrics":["curtain","clothing"],"priorities":[1,2,3,4]},"params":["prod_time_hours","rate_m_per_hour","curtain_demand_m","clothing_demand_m","curtain_profit_per_m","clothing_profit_per_m","overtime_cap_hours"],"variables":{"production_m[fabrics]":"continuous nonnegative","shortage_m[fabrics]":"continuous nonnegative","unused_hours":"continuous nonnegative","overtime_hours":"continuous nonnegative","excess_overtime_hours":"continuous nonnegative"},"constraints":["sum(production_m)/rate_m_per_hour + unused_hours - overtime_hours = prod_time_hours","overtime_hours - excess_overtime_hours <= overtime_cap_hours","production_m[f] + shortage_m[f] = demand_m[f] for each fabric f (sellable demand is also a production cap)","After each of priorities 1-3, constrain its expression <= its retrieved optimum"],"objective":{"sense":"lexicographic minimize","priorities":["unused_hours","excess_overtime_hours","sum(profit_per_m[f] * shortage_m[f])","overtime_hours"],"returned_objective":"priority 4 optimum in hours"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.fabrics = pyo.Set(
        initialize=["curtain", "clothing"], ordered=True
    )

    model.available_hours = pyo.Param(
        initialize=params["prod_time_hours"],
        within=pyo.NonNegativeReals,
    )
    model.production_rate = pyo.Param(
        initialize=params["rate_m_per_hour"],
        within=pyo.PositiveReals,
    )
    model.demand_m = pyo.Param(
        model.fabrics,
        initialize={
            "curtain": params["curtain_demand_m"],
            "clothing": params["clothing_demand_m"],
        },
        within=pyo.NonNegativeReals,
    )
    model.profit_per_m = pyo.Param(
        model.fabrics,
        initialize={
            "curtain": params["curtain_profit_per_m"],
            "clothing": params["clothing_profit_per_m"],
        },
        within=pyo.NonNegativeReals,
    )
    model.overtime_limit = pyo.Param(
        initialize=params["overtime_cap_hours"],
        within=pyo.NonNegativeReals,
    )

    model.production_m = pyo.Var(
        model.fabrics, domain=pyo.NonNegativeReals
    )
    model.shortage_m = pyo.Var(
        model.fabrics, domain=pyo.NonNegativeReals
    )
    model.unused_hours = pyo.Var(domain=pyo.NonNegativeReals)
    model.overtime_hours = pyo.Var(domain=pyo.NonNegativeReals)
    model.excess_overtime_hours = pyo.Var(domain=pyo.NonNegativeReals)

    model.production_time_balance = pyo.Constraint(
        expr=(
            sum(
                model.production_m[fabric]
                for fabric in model.fabrics
            )
            / model.production_rate
            + model.unused_hours
            - model.overtime_hours
            == model.available_hours
        )
    )

    # The overtime cap is a priority-2 goal, with excess allowed
    # and penalized before considering priorities 3 and 4.
    model.overtime_goal = pyo.Constraint(
        expr=(
            model.overtime_hours - model.excess_overtime_hours
            <= model.overtime_limit
        )
    )

    def demand_balance_rule(instance, fabric):
        return (
            instance.production_m[fabric]
            + instance.shortage_m[fabric]
            == instance.demand_m[fabric]
        )

    model.demand_balance = pyo.Constraint(
        model.fabrics, rule=demand_balance_rule
    )

    priority_expressions = [
        model.unused_hours,
        model.excess_overtime_hours,
        sum(
            model.profit_per_m[fabric] * model.shortage_m[fabric]
            for fabric in model.fabrics
        ),
        model.overtime_hours,
    ]

    model.fixed_priorities = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priority_expressions[0],
        sense=pyo.minimize,
    )

    # Sequential solves enforce strict preemptive priorities without
    # introducing arbitrary large objective weights.
    for priority_position, expression in enumerate(priority_expressions):
        model.goal_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            message = str(exc).lower()
            if (
                "a feasible solution was not found" in message
                or "no feasible solution" in message
            ):
                return {"objective": None, "status": "no_feasible_solution"}
            raise

        # Success is determined only by retrieving the objective value.
        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_position < len(priority_expressions) - 1:
            model.fixed_priorities.add(expression <= obj_val)

    return {"objective": obj_val, "status": "optimal"}