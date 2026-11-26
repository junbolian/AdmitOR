# IR: {"sets":{"T":[1,2,3,4,5,6]},"params":["raw_material_cost","labor_hours_per_unit","unit_price","initial_workers","initial_inventory","normal_wage","normal_hours_per_day","overtime_wage","working_days_per_month","max_overtime_hours_per_worker","outsourcing_cost","inventory_cost","stockout_cost","hiring_cost","firing_cost","demand[T]","min_final_inventory"],"variables":{"workers[T]":"nonnegative integer","hired[T]":"nonnegative integer","fired[T]":"nonnegative integer","production[T]":"nonnegative real","overtime_hours[T]":"nonnegative real","outsourced[T]":"nonnegative real","inventory[T]":"nonnegative real","backlog[T]":"nonnegative real"},"assumptions":["Stockouts are backorders charged per unit per month.","All demand must be fulfilled by the end of month 6.","Hiring and firing occur before each month's production.","Normal wages are paid for all scheduled normal hours, including idle hours.","Outsourcing cost includes outsourced materials."],"constraints":["workers[t]=previous_workers+hired[t]-fired[t]; previous_workers=initial_workers for t=1.","labor_hours_per_unit*production[t]<=normal_hours_per_day*working_days_per_month*workers[t]+overtime_hours[t].","overtime_hours[t]<=max_overtime_hours_per_worker*workers[t].","inventory[t]-backlog[t]=previous_inventory-previous_backlog+production[t]+outsourced[t]-demand[t]; initial backlog=0.","inventory[6]>=min_final_inventory.","backlog[6]=0."],"objective":"maximize unit_price*sum(demand[t])-sum(raw_material_cost*production[t]+normal_wage*normal_hours_per_day*working_days_per_month*workers[t]+overtime_wage*overtime_hours[t]+outsourcing_cost*outsourced[t]+inventory_cost*inventory[t]+stockout_cost*backlog[t]+hiring_cost*hired[t]+firing_cost*fired[t])"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 6)

    scalar_names = (
        "raw_material_cost",
        "labor_hours_per_unit",
        "unit_price",
        "initial_workers",
        "initial_inventory",
        "normal_wage",
        "normal_hours_per_day",
        "overtime_wage",
        "working_days_per_month",
        "max_overtime_hours_per_worker",
        "outsourcing_cost",
        "inventory_cost",
        "stockout_cost",
        "hiring_cost",
        "firing_cost",
        "min_final_inventory",
    )
    for parameter_name in scalar_names:
        setattr(
            model,
            parameter_name,
            pyo.Param(
                initialize=params[parameter_name],
                within=pyo.NonNegativeReals,
            ),
        )

    # Demand may be a six-element sequence or a mapping keyed by 1..6
    # (integer keys or their JSON string equivalents).
    demand_input = params["demand"]
    if isinstance(demand_input, Mapping):
        demand_values = {
            month: (
                demand_input[month]
                if month in demand_input
                else demand_input[str(month)]
            )
            for month in model.months
        }
    else:
        if len(demand_input) != 6:
            raise ValueError("demand must contain exactly six monthly values")
        demand_values = {
            month: demand_input[month - 1] for month in model.months
        }

    model.demand = pyo.Param(
        model.months,
        initialize=demand_values,
        within=pyo.NonNegativeReals,
    )

    model.workers = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.hired = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.fired = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.production = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.overtime_hours = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.outsourced = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.backlog = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def workforce_rule(plan, month):
        previous_workers = (
            plan.initial_workers if month == 1 else plan.workers[month - 1]
        )
        return (
            plan.workers[month]
            == previous_workers + plan.hired[month] - plan.fired[month]
        )

    model.workforce_balance = pyo.Constraint(
        model.months, rule=workforce_rule
    )

    def capacity_rule(plan, month):
        return (
            plan.labor_hours_per_unit * plan.production[month]
            <= plan.normal_hours_per_day
            * plan.working_days_per_month
            * plan.workers[month]
            + plan.overtime_hours[month]
        )

    model.production_capacity = pyo.Constraint(
        model.months, rule=capacity_rule
    )

    def overtime_rule(plan, month):
        return (
            plan.overtime_hours[month]
            <= plan.max_overtime_hours_per_worker * plan.workers[month]
        )

    model.overtime_limit = pyo.Constraint(
        model.months, rule=overtime_rule
    )

    def inventory_rule(plan, month):
        previous_inventory = (
            plan.initial_inventory if month == 1 else plan.inventory[month - 1]
        )
        previous_backlog = 0 if month == 1 else plan.backlog[month - 1]
        return (
            plan.inventory[month] - plan.backlog[month]
            == previous_inventory
            - previous_backlog
            + plan.production[month]
            + plan.outsourced[month]
            - plan.demand[month]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_rule
    )
    model.final_inventory_requirement = pyo.Constraint(
        expr=model.inventory[6] >= model.min_final_inventory
    )
    model.final_backlog_requirement = pyo.Constraint(
        expr=model.backlog[6] == 0
    )

    model.total_profit = pyo.Objective(
        expr=model.unit_price
        * sum(model.demand[month] for month in model.months)
        - sum(
            model.raw_material_cost * model.production[month]
            + model.normal_wage
            * model.normal_hours_per_day
            * model.working_days_per_month
            * model.workers[month]
            + model.overtime_wage * model.overtime_hours[month]
            + model.outsourcing_cost * model.outsourced[month]
            + model.inventory_cost * model.inventory[month]
            + model.stockout_cost * model.backlog[month]
            + model.hiring_cost * model.hired[month]
            + model.firing_cost * model.fired[month]
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_unavailable"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}