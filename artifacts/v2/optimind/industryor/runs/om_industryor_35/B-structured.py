# IR: {"sets":{"products":["A","B"],"processes":["I","II"]},"params":["time_I_A","time_I_B","time_II_A","time_II_B","capacity_I","capacity_II","profit_A","profit_B","min_units_A","min_units_B","target_profit","target_time_I","target_time_II"],"interpretation":"Capacities are regular-time limits; nonnegative, uncapped overtime is permitted. Process I must meet its exact time target; Process II must meet or exceed its utilization target. Production and profit minimums are mandatory.","variables":{"units[products]":"NonNegativeIntegers","overtime[processes]":"NonNegativeReals"},"expressions":{"hours[I]":"time_I_A*units[A]+time_I_B*units[B]","hours[II]":"time_II_A*units[A]+time_II_B*units[B]","total_profit":"profit_A*units[A]+profit_B*units[B]"},"constraints":["units[A]>=min_units_A","units[B]>=min_units_B","hours[I]<=capacity_I+overtime[I]","hours[II]<=capacity_II+overtime[II]","total_profit>=target_profit","hours[I]==target_time_I","hours[II]>=target_time_II"],"objective":"maximize total_profit"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["A", "B"], ordered=True)
    model.processes = pyo.Set(initialize=["I", "II"], ordered=True)

    model.processing_time = pyo.Param(
        model.processes,
        model.products,
        initialize={
            ("I", "A"): params["time_I_A"],
            ("I", "B"): params["time_I_B"],
            ("II", "A"): params["time_II_A"],
            ("II", "B"): params["time_II_B"],
        },
    )
    model.regular_capacity = pyo.Param(
        model.processes,
        initialize={
            "I": params["capacity_I"],
            "II": params["capacity_II"],
        },
    )
    model.unit_profit = pyo.Param(
        model.products,
        initialize={
            "A": params["profit_A"],
            "B": params["profit_B"],
        },
    )
    model.minimum_units = pyo.Param(
        model.products,
        initialize={
            "A": params["min_units_A"],
            "B": params["min_units_B"],
        },
    )
    model.profit_target = pyo.Param(initialize=params["target_profit"])
    model.process_time_target = pyo.Param(
        model.processes,
        initialize={
            "I": params["target_time_I"],
            "II": params["target_time_II"],
        },
    )

    model.units = pyo.Var(model.products, domain=pyo.NonNegativeIntegers)
    model.overtime = pyo.Var(model.processes, domain=pyo.NonNegativeReals)

    def hours_rule(instance, process):
        return sum(
            instance.processing_time[process, product] * instance.units[product]
            for product in instance.products
        )

    model.hours = pyo.Expression(model.processes, rule=hours_rule)
    model.total_profit = pyo.Expression(
        expr=sum(
            model.unit_profit[product] * model.units[product]
            for product in model.products
        )
    )

    def production_minimum_rule(instance, product):
        return instance.units[product] >= instance.minimum_units[product]

    model.production_minimum = pyo.Constraint(
        model.products, rule=production_minimum_rule
    )

    def capacity_with_overtime_rule(instance, process):
        return (
            instance.hours[process]
            <= instance.regular_capacity[process] + instance.overtime[process]
        )

    model.capacity_with_overtime = pyo.Constraint(
        model.processes, rule=capacity_with_overtime_rule
    )
    model.profit_minimum = pyo.Constraint(
        expr=model.total_profit >= model.profit_target
    )
    model.process_I_exact_time = pyo.Constraint(
        expr=model.hours["I"] == model.process_time_target["I"]
    )
    model.process_II_utilization = pyo.Constraint(
        expr=model.hours["II"] >= model.process_time_target["II"]
    )

    model.profit_objective = pyo.Objective(
        expr=model.total_profit, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.profit_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}