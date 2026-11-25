# IR: {"sets":{"P":["product_0","product_1","product_2","product_3"],"T":[0,1,2,3,4,5],"K":["grinder","drill","borer"]},"params":["profit_per_unit[P]","holding_cost","machine_capacity[K]","machine_time_req[K,P]","inventory_limit (scalar or P-indexed)","sales_limit[P,T]","target_inventory (scalar or P-indexed)","borer_downtime_period"],"variables":{"production[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0]","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for t > 0","sum_p machine_time_req[k,p]*production[p,t] <= machine_capacity[k], except capacity is zero for borer at borer_downtime_period","inventory[p,t] <= inventory_limit[p]","sales[p,t] <= sales_limit[p,t]","inventory[p,5] = target_inventory[p]"],"objective":"maximize sum_(p,t) profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t]"}

from collections.abc import Mapping, Sequence

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Indexed inputs accept sequences in the orders given in the IR, or
    dictionaries keyed by product/machine names and integer period indices.

    machine_time_req is machine-major: machine_time_req[machine][product].
    sales_limit is product-major: sales_limit[product][period].
    inventory_limit and target_inventory may be scalars or product-indexed.
    """

    products = ("product_0", "product_1", "product_2", "product_3")
    machines = ("grinder", "drill", "borer")
    periods = range(6)

    def indexed_value(data, label, position):
        if isinstance(data, Mapping):
            return data[label]
        return data[position]

    def product_value(data, product, position):
        if isinstance(data, Mapping):
            return data[product]
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            return data[position]
        return data

    profit_data = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    capacity_data = params["machine_capacity"]
    time_data = params["machine_time_req"]
    inventory_data = params["inventory_limit"]
    sales_data = params["sales_limit"]
    target_data = params["target_inventory"]
    downtime_period = params["borer_downtime_period"]

    profit = {
        product: indexed_value(profit_data, product, product_idx)
        for product_idx, product in enumerate(products)
    }
    capacity = {
        machine: indexed_value(capacity_data, machine, machine_idx)
        for machine_idx, machine in enumerate(machines)
    }
    time_requirement = {
        (machine, product): indexed_value(
            indexed_value(time_data, machine, machine_idx),
            product,
            product_idx,
        )
        for machine_idx, machine in enumerate(machines)
        for product_idx, product in enumerate(products)
    }
    inventory_limit = {
        product: product_value(inventory_data, product, product_idx)
        for product_idx, product in enumerate(products)
    }
    sales_limit = {
        (product, period): indexed_value(
            indexed_value(sales_data, product, product_idx),
            period,
            period,
        )
        for product_idx, product in enumerate(products)
        for period in periods
    }
    target_inventory = {
        product: product_value(target_data, product, product_idx)
        for product_idx, product in enumerate(products)
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.periods = pyo.RangeSet(0, 5)
    model.machines = pyo.Set(initialize=machines, ordered=True)

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def balance_rule(instance, product, period):
        if period == 0:
            return (
                instance.production[product, period]
                == instance.sales[product, period]
                + instance.inventory[product, period]
            )
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.flow_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )

    def capacity_rule(instance, machine, period):
        available_capacity = (
            0
            if machine == "borer" and period == downtime_period
            else capacity[machine]
        )
        return (
            sum(
                time_requirement[machine, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= available_capacity
        )

    model.capacity_constraints = pyo.Constraint(
        model.machines, model.periods, rule=capacity_rule
    )

    model.inventory_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period] <= inventory_limit[product]
        ),
    )
    model.sales_constraints = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period] <= sales_limit[product, period]
        ),
    )
    model.terminal_inventory_constraints = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 5] == target_inventory[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            profit[product] * model.sales[product, period]
            - holding_cost * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_unavailable"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}