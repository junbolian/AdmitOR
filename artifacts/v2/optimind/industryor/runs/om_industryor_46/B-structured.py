# IR: {"sets":{"products":["A","B"],"priorities":[1,2,3,4]},"params":["process_I_hours_A","process_I_hours_B","process_II_hours_A","process_II_hours_B","capacity_I","capacity_II","profit_A","profit_B","profit_target","min_units_A","min_units_B","overtime_reduction_A","overtime_reduction_B","max_overtime_II"],"variables":{"regular[product]":"nonnegative real units","overtime[product]":"nonnegative real units","profit_shortfall":"nonnegative real yuan","unit_shortfall[product]":"nonnegative real units","idle_I":"nonnegative real hours","idle_II":"nonnegative real hours"},"expressions":{"total[product]":"regular[product]+overtime[product]","overtime_loss":"sum(overtime_reduction[product]*overtime[product])","net_profit":"sum(profit[product]*total[product])-overtime_loss"},"constraints":["sum(process_I_hours[product]*total[product])+idle_I=capacity_I","sum(process_II_hours[product]*regular[product])+idle_II=capacity_II","sum(process_II_hours[product]*overtime[product])<=max_overtime_II","net_profit+profit_shortfall>=profit_target","total[product]+unit_shortfall[product]>=min_units[product]","after each of priorities 1,2,3, constrain its objective to be no greater than its attained optimum"],"objective":{"sense":"lexicographic minimize","priority_1":"profit_shortfall","priority_2":"sum(unit_shortfall[product])","priority_3":"idle_I+idle_II","priority_4":"overtime_loss"},"interpretation":"Continuous production goal programming; profit and contract targets are soft goals; processing capacities and overtime limit are hard constraints; overtime profit reductions apply to the profit target; equal-priority deviations have equal weights.","returned_objective":"priority_4 overtime_loss after optimizing and fixing priorities 1 through 3"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.priorities = pyo.RangeSet(1, 4)

    model.process_I_hours = pyo.Param(
        model.products,
        initialize={
            "A": params["process_I_hours_A"],
            "B": params["process_I_hours_B"],
        },
    )
    model.process_II_hours = pyo.Param(
        model.products,
        initialize={
            "A": params["process_II_hours_A"],
            "B": params["process_II_hours_B"],
        },
    )
    model.capacity_I = pyo.Param(initialize=params["capacity_I"])
    model.capacity_II = pyo.Param(initialize=params["capacity_II"])
    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            "A": params["profit_A"],
            "B": params["profit_B"],
        },
    )
    model.profit_target = pyo.Param(initialize=params["profit_target"])
    model.minimum_units = pyo.Param(
        model.products,
        initialize={
            "A": params["min_units_A"],
            "B": params["min_units_B"],
        },
    )
    model.overtime_reduction = pyo.Param(
        model.products,
        initialize={
            "A": params["overtime_reduction_A"],
            "B": params["overtime_reduction_B"],
        },
    )
    model.max_overtime_II = pyo.Param(initialize=params["max_overtime_II"])

    model.regular = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.products, domain=pyo.NonNegativeReals)
    model.profit_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.unit_shortfall = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )
    model.idle_I = pyo.Var(domain=pyo.NonNegativeReals)
    model.idle_II = pyo.Var(domain=pyo.NonNegativeReals)

    def total_units_rule(problem, product):
        return problem.regular[product] + problem.overtime[product]

    model.total_units = pyo.Expression(
        model.products, rule=total_units_rule
    )
    model.overtime_loss = pyo.Expression(
        expr=sum(
            model.overtime_reduction[product] * model.overtime[product]
            for product in model.products
        )
    )
    model.net_profit = pyo.Expression(
        expr=sum(
            model.unit_profit[product] * model.total_units[product]
            for product in model.products
        )
        - model.overtime_loss
    )

    model.process_I_balance = pyo.Constraint(
        expr=sum(
            model.process_I_hours[product] * model.total_units[product]
            for product in model.products
        )
        + model.idle_I
        == model.capacity_I
    )
    model.process_II_regular_balance = pyo.Constraint(
        expr=sum(
            model.process_II_hours[product] * model.regular[product]
            for product in model.products
        )
        + model.idle_II
        == model.capacity_II
    )
    model.process_II_overtime_limit = pyo.Constraint(
        expr=sum(
            model.process_II_hours[product] * model.overtime[product]
            for product in model.products
        )
        <= model.max_overtime_II
    )
    model.profit_goal = pyo.Constraint(
        expr=model.net_profit + model.profit_shortfall
        >= model.profit_target
    )

    def contract_goal_rule(problem, product):
        return (
            problem.total_units[product] + problem.unit_shortfall[product]
            >= problem.minimum_units[product]
        )

    model.contract_goals = pyo.Constraint(
        model.products, rule=contract_goal_rule
    )

    def goal_cost_rule(problem, priority):
        if priority == 1:
            return problem.profit_shortfall
        if priority == 2:
            return sum(
                problem.unit_shortfall[product]
                for product in problem.products
            )
        if priority == 3:
            return problem.idle_I + problem.idle_II
        return problem.overtime_loss

    model.goal_cost = pyo.Expression(
        model.priorities, rule=goal_cost_rule
    )
    model.priority_locks = pyo.ConstraintList()
    model.objective = pyo.Objective(
        expr=model.goal_cost[1], sense=pyo.minimize
    )

    for priority in model.priorities:
        model.objective.set_value(model.goal_cost[priority])

        # Clear previous solutions so retrieval cannot use stale values.
        for variable in model.component_data_objects(pyo.Var):
            variable.set_value(None)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "infeasible_or_failed"}

        try:
            obj_val = float(pyo.value(model.objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        if priority < 4:
            model.priority_locks.add(
                model.goal_cost[priority] <= obj_val
            )

    return {"objective": obj_val, "status": "optimal"}