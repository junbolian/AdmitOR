# IR: {"sets":{"products":["A","B"],"processes":["manufacturing","assembly","inspection"],"priorities":[1,2,3]},"params":["man_hours_A","man_hours_B","asm_hours_A","asm_hours_B","insp_hours_A","insp_hours_B","price_A","price_B","cap_manufacturing","cap_assembly","cap_inspection","cost_manufacturing","cost_assembly","cost_inspection","profit_goal","min_A_goal"],"derived":{"hours":{"manufacturing":{"A":"man_hours_A","B":"man_hours_B"},"assembly":{"A":"asm_hours_A","B":"asm_hours_B"},"inspection":{"A":"insp_hours_A","B":"insp_hours_B"}},"unit_profit[t]":"price[t]-sum(cost[r]*hours[r,t] for r in processes)"},"variables":{"production[t]":"NonNegativeIntegers","profit_shortfall":"NonNegativeReals","A_shortfall":"NonNegativeReals","idle[r]":"NonNegativeReals"},"constraints":["sum(hours[r,t]*production[t] for t in products)+idle[r]=capacity[r] for each process r; nonnegative idle forbids overtime","sum(unit_profit[t]*production[t] for t in products)+profit_shortfall>=profit_goal","production[A]+A_shortfall>=min_A_goal","After each of priorities 1 and 2, fix its objective expression at its retrieved optimum."],"objective":{"sense":"minimize","method":"sequential lexicographic optimization","priority_1":"profit_shortfall","priority_2":"A_shortfall","priority_3":"sum(cost[r]*idle[r] for r in processes)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.processes = pyo.Set(
        initialize=["manufacturing", "assembly", "inspection"],
        ordered=True,
    )

    model.hours = pyo.Param(
        model.processes,
        model.products,
        initialize={
            ("manufacturing", "A"): params["man_hours_A"],
            ("manufacturing", "B"): params["man_hours_B"],
            ("assembly", "A"): params["asm_hours_A"],
            ("assembly", "B"): params["asm_hours_B"],
            ("inspection", "A"): params["insp_hours_A"],
            ("inspection", "B"): params["insp_hours_B"],
        },
        within=pyo.Reals,
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize={
            "A": params["price_A"],
            "B": params["price_B"],
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.processes,
        initialize={
            "manufacturing": params["cap_manufacturing"],
            "assembly": params["cap_assembly"],
            "inspection": params["cap_inspection"],
        },
        within=pyo.Reals,
    )
    model.hourly_cost = pyo.Param(
        model.processes,
        initialize={
            "manufacturing": params["cost_manufacturing"],
            "assembly": params["cost_assembly"],
            "inspection": params["cost_inspection"],
        },
        within=pyo.Reals,
    )
    model.profit_target = pyo.Param(
        initialize=params["profit_goal"], within=pyo.Reals
    )
    model.A_target = pyo.Param(
        initialize=params["min_A_goal"], within=pyo.Reals
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.A_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle = pyo.Var(model.processes, domain=pyo.NonNegativeReals)

    def unit_profit_rule(current_model, product):
        return current_model.selling_price[product] - sum(
            current_model.hourly_cost[process]
            * current_model.hours[process, product]
            for process in current_model.processes
        )

    model.unit_profit = pyo.Expression(
        model.products, rule=unit_profit_rule
    )
    model.weekly_profit = pyo.Expression(
        expr=sum(
            model.unit_profit[product] * model.production[product]
            for product in model.products
        )
    )

    def capacity_rule(current_model, process):
        return (
            sum(
                current_model.hours[process, product]
                * current_model.production[product]
                for product in current_model.products
            )
            + current_model.idle[process]
            == current_model.capacity[process]
        )

    model.capacity_balance = pyo.Constraint(
        model.processes, rule=capacity_rule
    )
    model.profit_goal_constraint = pyo.Constraint(
        expr=model.weekly_profit + model.profit_shortfall
        >= model.profit_target
    )
    model.A_goal_constraint = pyo.Constraint(
        expr=model.production["A"] + model.A_shortfall >= model.A_target
    )

    model.weighted_idle_cost = pyo.Expression(
        expr=sum(
            model.hourly_cost[process] * model.idle[process]
            for process in model.processes
        )
    )
    model.priority_locks = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.profit_shortfall, sense=pyo.minimize
    )

    priority_expressions = (
        model.profit_shortfall,
        model.A_shortfall,
        model.weighted_idle_cost,
    )

    for priority_position, expression in enumerate(priority_expressions):
        model.goal_objective.set_value(expression)

        try:
            Highs().solve(model)
        except RuntimeError as exc:
            if "a feasible solution was not found" in str(exc).lower():
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

        if priority_position < len(priority_expressions) - 1:
            model.priority_locks.add(expression == obj_val)

    return {"objective": obj_val, "status": "optimal"}