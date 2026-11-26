# IR: {"sets":{"products":["A","B"],"priorities":[1,2,3,4]},"params":["profit_A","profit_B","profit_target","time_I_A","time_I_B","time_II_A","time_II_B","cap_I","cap_II","overtime_cap_II","min_A","min_B","overtime_penalty_A","overtime_penalty_B"],"variables":{"regular[products]":"nonnegative continuous units","overtime[products]":"nonnegative continuous units","profit_shortfall":"nonnegative continuous RMB","contract_shortfall[products]":"nonnegative continuous units","idle_I":"nonnegative continuous hours","unused_II":"nonnegative continuous hours"},"expressions":{"production[j]":"regular[j]+overtime[j]","hours_I":"sum(time_I[j]*production[j])","regular_hours_II":"sum(time_II[j]*regular[j])","overtime_hours_II":"sum(time_II[j]*overtime[j])","overtime_loss":"sum(overtime_penalty[j]*overtime[j])","net_profit":"sum(profit[j]*production[j])-overtime_loss"},"constraints":["net_profit+profit_shortfall>=profit_target","production[j]+contract_shortfall[j]>=minimum[j] for each product j","hours_I+idle_I=cap_I","regular_hours_II<=cap_II","overtime_hours_II<=overtime_cap_II","regular_hours_II+overtime_hours_II+unused_II=cap_II+overtime_cap_II","after each successful priority except the last, constrain its objective expression<=its attained optimum"],"objective":{"sense":"lexicographic minimization","levels":["profit_shortfall","sum(contract_shortfall[j])","idle_I+unused_II","overtime_loss"],"returned_objective":"final-priority overtime_loss subject to all preceding priority optima"}}
#
# Production quantities are continuous, as no integrality requirement is stated.
# At priority 3, the two goals receive equal weight because both measure hours.
# Process II maximization uses its total regular-plus-overtime capacity as a target.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = {
        "A": params["profit_A"],
        "B": params["profit_B"],
    }
    profit_target = params["profit_target"]

    time_I = {
        "A": params["time_I_A"],
        "B": params["time_I_B"],
    }
    time_II = {
        "A": params["time_II_A"],
        "B": params["time_II_B"],
    }

    cap_I = params["cap_I"]
    cap_II = params["cap_II"]
    overtime_cap_II = params["overtime_cap_II"]

    minimum = {
        "A": params["min_A"],
        "B": params["min_B"],
    }
    overtime_penalty = {
        "A": params["overtime_penalty_A"],
        "B": params["overtime_penalty_B"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=["A", "B"], ordered=True)

    # Units classified by whether process II occurs in regular or overtime hours.
    model.regular = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.contract_shortfall = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.idle_I = pyo.Var(domain=pyo.NonNegativeReals)
    model.unused_II = pyo.Var(domain=pyo.NonNegativeReals)

    model.production = pyo.Expression(
        model.products,
        rule=lambda mod, product: (
            mod.regular[product] + mod.overtime[product]
        ),
    )

    model.hours_I = pyo.Expression(
        expr=sum(
            time_I[product] * model.production[product]
            for product in model.products
        )
    )
    model.regular_hours_II = pyo.Expression(
        expr=sum(
            time_II[product] * model.regular[product]
            for product in model.products
        )
    )
    model.overtime_hours_II = pyo.Expression(
        expr=sum(
            time_II[product] * model.overtime[product]
            for product in model.products
        )
    )
    model.overtime_loss = pyo.Expression(
        expr=sum(
            overtime_penalty[product] * model.overtime[product]
            for product in model.products
        )
    )
    model.net_profit = pyo.Expression(
        expr=sum(
            profit[product] * model.production[product]
            for product in model.products
        ) - model.overtime_loss
    )

    model.profit_goal = pyo.Constraint(
        expr=model.net_profit + model.profit_shortfall >= profit_target
    )
    model.contract_goals = pyo.Constraint(
        model.products,
        rule=lambda mod, product: (
            mod.production[product] + mod.contract_shortfall[product]
            >= minimum[product]
        ),
    )

    # This equality also enforces the hard process I capacity limit.
    model.process_I_balance = pyo.Constraint(
        expr=model.hours_I + model.idle_I == cap_I
    )
    model.process_II_regular_limit = pyo.Constraint(
        expr=model.regular_hours_II <= cap_II
    )
    model.process_II_overtime_limit = pyo.Constraint(
        expr=model.overtime_hours_II <= overtime_cap_II
    )
    model.process_II_goal_balance = pyo.Constraint(
        expr=(
            model.regular_hours_II
            + model.overtime_hours_II
            + model.unused_II
            == cap_II + overtime_cap_II
        )
    )

    priority_expressions = (
        model.profit_shortfall,
        sum(
            model.contract_shortfall[product]
            for product in model.products
        ),
        model.idle_I + model.unused_II,
        model.overtime_loss,
    )

    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=priority_expressions[0],
        sense=pyo.minimize,
    )

    for priority_index, expression in enumerate(priority_expressions):
        model.goal_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            # APPsi raises this specific error when no feasible solution
            # is available to load. Unexpected runtime errors propagate.
            message = str(exc).lower()
            if "a feasible solution was not found" in message:
                return {
                    "objective": None,
                    "status": "no_feasible_solution",
                }
            raise

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except ValueError:
            return {
                "objective": None,
                "status": "objective_unavailable",
            }

        if priority_index < len(priority_expressions) - 1:
            model.priority_locks.add(expression <= obj_val)

    return {"objective": obj_val, "status": "optimal"}