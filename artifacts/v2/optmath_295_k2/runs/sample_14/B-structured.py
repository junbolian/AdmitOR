# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4],"K":[0,1,2],"machine_order":["grinders","drills","borers"]},"params":{"profit_per_unit":"real[P]","holding_cost_per_unit_per_period":"nonnegative real","machine_capacity_per_period":"nonnegative real[K]","machine_time_per_unit":"nonnegative matrix; accept K-by-P (3x4) or P-by-K (4x3), normalize to a[K,P]","period0_borer_capacity":"nonnegative real","inventory_limit_per_product_per_period":"nonnegative real","sales_limit":"nonnegative real[P,T]","target_inventory_end_period4":"nonnegative scalar or nonnegative real[P]; broadcast scalar"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["For each p: production[p,0] = sales[p,0] + inventory[p,0].","For each p,t>0: inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t].","For each k,t: sum_p a[k,p]*production[p,t] <= period0_borer_capacity when k=2,t=0; otherwise <= machine_capacity_per_period[k].","For each p,t: inventory[p,t] <= inventory_limit_per_product_per_period.","For each p,t: sales[p,t] <= sales_limit[p,t].","For each p: inventory[p,4] = target_inventory_end_period4[p]."],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_data = params["profit_per_unit"]
    holding_cost_data = params["holding_cost_per_unit_per_period"]
    capacity_data = params["machine_capacity_per_period"]
    machine_time_data = params["machine_time_per_unit"]
    period0_borer_data = params["period0_borer_capacity"]
    inventory_limit_data = params["inventory_limit_per_product_per_period"]
    sales_limit_data = params["sales_limit"]
    target_data = params["target_inventory_end_period4"]

    # Recognize matrix orientation before indexing its entries.
    if len(machine_time_data) == 3 and all(
        len(machine_time_data[machine]) == 4 for machine in range(3)
    ):
        processing_times = {
            (machine, product): machine_time_data[machine][product]
            for machine in range(3)
            for product in range(4)
        }
    elif len(machine_time_data) == 4 and all(
        len(machine_time_data[product]) == 3 for product in range(4)
    ):
        processing_times = {
            (machine, product): machine_time_data[product][machine]
            for machine in range(3)
            for product in range(4)
        }
    else:
        return {"objective": None, "status": "invalid_machine_time_shape"}

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 4)
    model.machines = pyo.RangeSet(0, 2)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profit_data[product],
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        initialize=holding_cost_data,
        within=pyo.NonNegativeReals,
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize=lambda mdl, machine: capacity_data[machine],
        within=pyo.NonNegativeReals,
    )
    model.processing_time = pyo.Param(
        model.machines,
        model.products,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )
    model.initial_borer_capacity = pyo.Param(
        initialize=period0_borer_data,
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity = pyo.Param(
        initialize=inventory_limit_data,
        within=pyo.NonNegativeReals,
    )
    model.sales_capacity = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: sales_limit_data[product][period],
        within=pyo.NonNegativeReals,
    )

    def target_initializer(mdl, product):
        if hasattr(target_data, "__getitem__"):
            return target_data[product]
        return target_data

    model.ending_target = pyo.Param(
        model.products,
        initialize=target_initializer,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.sales = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.inventory = pyo.Var(
        model.products,
        model.periods,
        domain=pyo.NonNegativeReals,
    )

    def balance_rule(mdl, product, period):
        if period == 0:
            return (
                mdl.production[product, period]
                == mdl.sales[product, period] + mdl.inventory[product, period]
            )
        return (
            mdl.inventory[product, period - 1] + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products,
        model.periods,
        rule=balance_rule,
    )

    def machine_capacity_rule(mdl, machine, period):
        capacity = (
            mdl.initial_borer_capacity
            if machine == 2 and period == 0
            else mdl.machine_capacity[machine]
        )
        return (
            sum(
                mdl.processing_time[machine, product]
                * mdl.production[product, period]
                for product in mdl.products
            )
            <= capacity
        )

    model.machine_capacity_limits = pyo.Constraint(
        model.machines,
        model.periods,
        rule=machine_capacity_rule,
    )
    model.inventory_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_capacity
        ),
    )
    model.sales_limits = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.sales[product, period] <= mdl.sales_capacity[product, period]
        ),
    )
    model.ending_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 4] == mdl.ending_target[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}