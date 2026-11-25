# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4],"K":[0,1,2],"machine_order":["grinders","drills","borers"]},"params":{"profit_per_unit":"P -> real","holding_cost_per_unit_per_period":"scalar real","machine_capacity_per_period":"K -> nonnegative real","machine_time_per_unit":"P x K -> nonnegative real (rows products, columns machines)","period0_borer_capacity":"scalar nonnegative real","inventory_limit_per_product_per_period":"scalar nonnegative real","sales_limit":"P x T -> nonnegative real","target_inventory_end_period4":"scalar nonnegative real"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t>0","sum(machine_time_per_unit[p,k]*production[p,t] for p in P) <= (period0_borer_capacity if k=2 and t=0 else machine_capacity_per_period[k]) for k in K, t in T","inventory[p,t] <= inventory_limit_per_product_per_period for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","inventory[p,4] = target_inventory_end_period4 for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve with product-major machine times and product-major sales limits."""
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 3)
    model.periods = pyo.RangeSet(0, 4)
    model.machines = pyo.RangeSet(0, 2)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
        within=pyo.Reals,
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_per_period"],
        within=pyo.Reals,
    )
    model.machine_capacity = pyo.Param(
        model.machines,
        initialize=lambda mdl, machine: params["machine_capacity_per_period"][machine],
        within=pyo.NonNegativeReals,
    )
    model.machine_time = pyo.Param(
        model.products,
        model.machines,
        initialize=lambda mdl, product, machine: params["machine_time_per_unit"][
            product
        ][machine],
        within=pyo.NonNegativeReals,
    )
    model.initial_borer_capacity = pyo.Param(
        initialize=params["period0_borer_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_limit_per_product_per_period"],
        within=pyo.NonNegativeReals,
    )
    model.sales_capacity = pyo.Param(
        model.products,
        model.periods,
        initialize=lambda mdl, product, period: params["sales_limit"][product][period],
        within=pyo.NonNegativeReals,
    )
    model.ending_inventory_target = pyo.Param(
        initialize=params["target_inventory_end_period4"],
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.products, rule=initial_balance_rule
    )

    def inventory_balance_rule(mdl, product, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.inventory[product, period - 1] + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    def machine_capacity_rule(mdl, machine, period):
        capacity = (
            mdl.initial_borer_capacity
            if machine == 2 and period == 0
            else mdl.machine_capacity[machine]
        )
        return (
            sum(
                mdl.machine_time[product, machine] * mdl.production[product, period]
                for product in mdl.products
            )
            <= capacity
        )

    model.machine_capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=machine_capacity_rule
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
    model.target_inventory = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 4] == mdl.ending_inventory_target
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
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}