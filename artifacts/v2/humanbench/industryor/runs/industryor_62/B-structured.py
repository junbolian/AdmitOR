# IR: {"sets":{"products":["A","B"],"goals":["profit","A_min","B_min","procI","procII"]},"params":["profit_A","profit_B","time_procI_A","time_procI_B","time_procII_A","time_procII_B","cap_procI","cap_procII","profit_target","min_A","min_B","procI_target"],"variables":{"production[products]":"NonNegativeReals","under[goals]":"NonNegativeReals","over[goals]":"NonNegativeReals"},"constraints":["hours_I = time_procI_A*production[A] + time_procI_B*production[B] <= cap_procI","profit_A*production[A] + profit_B*production[B] + under[profit] - over[profit] = profit_target","production[A] + under[A_min] - over[A_min] = min_A","production[B] + under[B_min] - over[B_min] = min_B","hours_I + under[procI] - over[procI] = procI_target","time_procII_A*production[A] + time_procII_B*production[B] + under[procII] - over[procII] = cap_procII"],"objective":{"sense":"lexicographic_minimize","priorities":["under[profit]","under[A_min] + under[B_min]","under[procI] + over[procI] + under[procII] - over[procII]"],"returned_value":"optimal third-priority objective"}}
#
# Modeling conventions:
# - Production is continuous because no integrality requirement is specified.
# - Process I capacity is a hard constraint.
# - Process II capacity is a soft reference level because overtime is allowed.
# - Within each priority, stated goals have equal unit weights.
# - At priority 3, under[procII] - over[procII] equals
#   cap_procII - hours_II, so minimizing it maximizes Process II hours,
#   including hours beyond regular capacity.
# - Priorities are enforced by sequential solves, fixing each earlier optimum.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    time_procI_A = params["time_procI_A"]
    time_procI_B = params["time_procI_B"]
    time_procII_A = params["time_procII_A"]
    time_procII_B = params["time_procII_B"]
    cap_procI = params["cap_procI"]
    cap_procII = params["cap_procII"]
    profit_target = params["profit_target"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    procI_target = params["procI_target"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.goals = pyo.Set(
        initialize=["profit", "A_min", "B_min", "procI", "procII"],
        ordered=True,
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.under = pyo.Var(model.goals, domain=pyo.NonNegativeReals)
    model.over = pyo.Var(model.goals, domain=pyo.NonNegativeReals)

    model.weekly_profit = pyo.Expression(
        expr=profit_A * model.production["A"]
        + profit_B * model.production["B"]
    )
    model.hours_I = pyo.Expression(
        expr=time_procI_A * model.production["A"]
        + time_procI_B * model.production["B"]
    )
    model.hours_II = pyo.Expression(
        expr=time_procII_A * model.production["A"]
        + time_procII_B * model.production["B"]
    )

    model.process_I_capacity = pyo.Constraint(
        expr=model.hours_I <= cap_procI
    )

    model.profit_goal = pyo.Constraint(
        expr=model.weekly_profit
        + model.under["profit"]
        - model.over["profit"]
        == profit_target
    )
    model.contract_A_goal = pyo.Constraint(
        expr=model.production["A"]
        + model.under["A_min"]
        - model.over["A_min"]
        == min_A
    )
    model.contract_B_goal = pyo.Constraint(
        expr=model.production["B"]
        + model.under["B_min"]
        - model.over["B_min"]
        == min_B
    )
    model.process_I_goal = pyo.Constraint(
        expr=model.hours_I
        + model.under["procI"]
        - model.over["procI"]
        == procI_target
    )
    model.process_II_goal = pyo.Constraint(
        expr=model.hours_II
        + model.under["procII"]
        - model.over["procII"]
        == cap_procII
    )

    model.priority_one = pyo.Expression(expr=model.under["profit"])
    model.priority_two = pyo.Expression(
        expr=model.under["A_min"] + model.under["B_min"]
    )
    model.priority_three = pyo.Expression(
        expr=model.under["procI"]
        + model.over["procI"]
        + model.under["procII"]
        - model.over["procII"]
    )

    priority_expressions = (
        model.priority_one,
        model.priority_two,
        model.priority_three,
    )

    model.fixed_priorities = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.priority_one,
        sense=pyo.minimize,
    )

    for priority_index, priority_expression in enumerate(priority_expressions):
        model.goal_objective.set_value(priority_expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solver_failed"}

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority_index < len(priority_expressions) - 1:
            model.fixed_priorities.add(priority_expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}