# IR: {"sets":{"T":[1,2,3,4,5,6]},"params":["sales_price","raw_material_cost","outsourcing_cost","inventory_holding_cost","backorder_cost","labor_hours_per_unit","regular_hours_per_worker","regular_wage_per_hour","max_overtime_hours_per_worker","overtime_wage_per_hour","hiring_cost","firing_cost","initial_workforce","initial_inventory","terminal_min_inventory","demand[T]"],"variables":{"production[T]":"nonnegative integer","outsourcing[T]":"nonnegative integer","workforce[T]":"nonnegative integer","hires[T]":"nonnegative integer","fires[T]":"nonnegative integer","inventory[T]":"nonnegative integer","backorders[T]":"nonnegative integer","shipments[T]":"nonnegative integer","overtime_hours[T]":"nonnegative real"},"constraints":["workforce[t] = (initial_workforce if t=1 else workforce[t-1]) + hires[t] - fires[t]","labor_hours_per_unit*production[t] <= regular_hours_per_worker*workforce[t] + overtime_hours[t]","overtime_hours[t] <= max_overtime_hours_per_worker*workforce[t]","inventory[t] = (initial_inventory if t=1 else inventory[t-1]) + production[t] + outsourcing[t] - shipments[t]","backorders[t] = (0 if t=1 else backorders[t-1]) + demand[t] - shipments[t]","inventory[6] >= terminal_min_inventory","backorders[6] = 0"],"objective":"maximize sum_t(sales_price*shipments[t] - raw_material_cost*production[t] - outsourcing_cost*outsourcing[t] - inventory_holding_cost*inventory[t] - backorder_cost*backorders[t] - regular_wage_per_hour*regular_hours_per_worker*workforce[t] - overtime_wage_per_hour*overtime_hours[t] - hiring_cost*hires[t] - firing_cost*fires[t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six-month plan; params['demand'] is ordered January–June."""
    demand_values = tuple(params["demand"])
    if len(demand_values) != 6:
        raise ValueError("params['demand'] must contain six monthly values.")

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 6)

    model.sales_price = pyo.Param(
        initialize=params["sales_price"], within=pyo.NonNegativeReals
    )
    model.raw_material_cost = pyo.Param(
        initialize=params["raw_material_cost"], within=pyo.NonNegativeReals
    )
    model.outsourcing_cost = pyo.Param(
        initialize=params["outsourcing_cost"], within=pyo.NonNegativeReals
    )
    model.inventory_holding_cost = pyo.Param(
        initialize=params["inventory_holding_cost"], within=pyo.NonNegativeReals
    )
    model.backorder_cost = pyo.Param(
        initialize=params["backorder_cost"], within=pyo.NonNegativeReals
    )
    model.labor_hours_per_unit = pyo.Param(
        initialize=params["labor_hours_per_unit"], within=pyo.PositiveReals
    )
    model.regular_hours_per_worker = pyo.Param(
        initialize=params["regular_hours_per_worker"], within=pyo.NonNegativeReals
    )
    model.regular_wage_per_hour = pyo.Param(
        initialize=params["regular_wage_per_hour"], within=pyo.NonNegativeReals
    )
    model.max_overtime_hours_per_worker = pyo.Param(
        initialize=params["max_overtime_hours_per_worker"],
        within=pyo.NonNegativeReals,
    )
    model.overtime_wage_per_hour = pyo.Param(
        initialize=params["overtime_wage_per_hour"], within=pyo.NonNegativeReals
    )
    model.hiring_cost = pyo.Param(
        initialize=params["hiring_cost"], within=pyo.NonNegativeReals
    )
    model.firing_cost = pyo.Param(
        initialize=params["firing_cost"], within=pyo.NonNegativeReals
    )
    model.initial_workforce = pyo.Param(
        initialize=params["initial_workforce"], within=pyo.NonNegativeIntegers
    )
    model.initial_inventory = pyo.Param(
        initialize=params["initial_inventory"], within=pyo.NonNegativeIntegers
    )
    model.terminal_min_inventory = pyo.Param(
        initialize=params["terminal_min_inventory"], within=pyo.NonNegativeReals
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: demand_values[t - 1] for t in range(1, 7)},
        within=pyo.NonNegativeIntegers,
    )

    model.production = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.outsourcing = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.workforce = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.hires = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.fires = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.backorders = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.shipments = pyo.Var(model.months, domain=pyo.NonNegativeIntegers)
    model.overtime_hours = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def workforce_balance_rule(model, t):
        previous_workforce = (
            model.initial_workforce if t == 1 else model.workforce[t - 1]
        )
        return (
            model.workforce[t]
            == previous_workforce + model.hires[t] - model.fires[t]
        )

    model.workforce_balance = pyo.Constraint(
        model.months, rule=workforce_balance_rule
    )

    def production_capacity_rule(model, t):
        return (
            model.labor_hours_per_unit * model.production[t]
            <= model.regular_hours_per_worker * model.workforce[t]
            + model.overtime_hours[t]
        )

    model.production_capacity = pyo.Constraint(
        model.months, rule=production_capacity_rule
    )

    def overtime_limit_rule(model, t):
        return (
            model.overtime_hours[t]
            <= model.max_overtime_hours_per_worker * model.workforce[t]
        )

    model.overtime_limit = pyo.Constraint(
        model.months, rule=overtime_limit_rule
    )

    def inventory_balance_rule(model, t):
        previous_inventory = (
            model.initial_inventory if t == 1 else model.inventory[t - 1]
        )
        return (
            model.inventory[t]
            == previous_inventory
            + model.production[t]
            + model.outsourcing[t]
            - model.shipments[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    def backorder_balance_rule(model, t):
        previous_backorders = 0 if t == 1 else model.backorders[t - 1]
        return (
            model.backorders[t]
            == previous_backorders + model.demand[t] - model.shipments[t]
        )

    model.backorder_balance = pyo.Constraint(
        model.months, rule=backorder_balance_rule
    )

    model.terminal_inventory_requirement = pyo.Constraint(
        expr=model.inventory[6] >= model.terminal_min_inventory
    )
    model.terminal_backorder_clearance = pyo.Constraint(
        expr=model.backorders[6] == 0
    )

    model.total_net_profit = pyo.Objective(
        expr=sum(
            model.sales_price * model.shipments[t]
            - model.raw_material_cost * model.production[t]
            - model.outsourcing_cost * model.outsourcing[t]
            - model.inventory_holding_cost * model.inventory[t]
            - model.backorder_cost * model.backorders[t]
            - model.regular_wage_per_hour
            * model.regular_hours_per_worker
            * model.workforce[t]
            - model.overtime_wage_per_hour * model.overtime_hours[t]
            - model.hiring_cost * model.hires[t]
            - model.firing_cost * model.fires[t]
            for t in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when automatic solution loading finds no solution.
        # Unexpected runtime errors must propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Success depends solely on whether the objective value is retrievable.
    try:
        obj_val = float(pyo.value(model.total_net_profit))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}