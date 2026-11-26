# IR: {"sets":{"P":["A1","A2","A3"],"T":[0,1,2,3]},"params":{"demand_A1":"length-4 array","demand_A2":"length-4 array","demand_A3":"length-4 array","price":"length-3 array","production_cost":"length-3 array","activation_cost":"length-3 array","production_quota":"length-3 array","min_batch_size":"length-3 array","production_days":"length-4 array","storage_cost":"length-3 array","storage_capacity":"scalar"},"interpretation":{"quota":"daily quota multiplied by production_days, as implied by the production calendar","minimum_batch":"monthly minimum","demand":"sales upper bound; unmet demand is lost","initial_inventory":0,"revenue":"sales revenue minus production, activation, and storage costs"},"variables":{"production[p,t]":"nonnegative continuous","sales[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous; end-of-month inventory","line_on[p,t]":"binary"},"constraints":["sales[p,t] <= demand[p,t]","production[p,t] <= production_quota[p]*production_days[t]*line_on[p,t]","production[p,t] >= min_batch_size[p]*line_on[p,t]","inventory[p,t] = (0 if t=0 else inventory[p,t-1]) + production[p,t] - sales[p,t]","sum_p inventory[p,t] <= storage_capacity"],"objective":"maximize sum_(p,t)(price[p]*sales[p,t] - production_cost[p]*production[p,t] - activation_cost[p]*line_on[p,t] - storage_cost[p]*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Product arrays are ordered A1, A2, A3.
    Monthly arrays are ordered January, February, March, April.

    Production quotas are interpreted as daily limits, multiplied by the
    supplied production days. Minimum batch sizes apply monthly.
    """
    products = ("A1", "A2", "A3")
    months = range(4)

    demand_arrays = {
        "A1": params["demand_A1"],
        "A2": params["demand_A2"],
        "A3": params["demand_A3"],
    }
    prices = params["price"]
    production_costs = params["production_cost"]
    activation_costs = params["activation_cost"]
    quotas = params["production_quota"]
    minimum_batches = params["min_batch_size"]
    days = params["production_days"]
    storage_costs = params["storage_cost"]
    storage_capacity = params["storage_capacity"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=products, ordered=True)
    model.months = pyo.Set(initialize=months, ordered=True)

    model.demand = pyo.Param(
        model.products,
        model.months,
        initialize={
            (product, month): demand_arrays[product][month]
            for product in products
            for month in months
        },
        within=pyo.NonNegativeReals,
    )

    product_parameters = (
        ("unit_price", prices),
        ("unit_production_cost", production_costs),
        ("line_activation_cost", activation_costs),
        ("daily_quota", quotas),
        ("minimum_batch", minimum_batches),
        ("unit_storage_cost", storage_costs),
    )
    for component_name, values in product_parameters:
        model.add_component(
            component_name,
            pyo.Param(
                model.products,
                initialize={
                    product: values[position]
                    for position, product in enumerate(products)
                },
                within=pyo.NonNegativeReals,
            ),
        )

    model.days_available = pyo.Param(
        model.months,
        initialize={month: days[month] for month in months},
        within=pyo.NonNegativeReals,
    )
    model.inventory_capacity = pyo.Param(
        initialize=storage_capacity,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.months, domain=pyo.NonNegativeReals
    )
    model.line_on = pyo.Var(
        model.products, model.months, domain=pyo.Binary
    )

    def sales_limit_rule(instance, product, month):
        return instance.sales[product, month] <= instance.demand[product, month]

    model.sales_limit = pyo.Constraint(
        model.products, model.months, rule=sales_limit_rule
    )

    def production_limit_rule(instance, product, month):
        return instance.production[product, month] <= (
            instance.daily_quota[product]
            * instance.days_available[month]
            * instance.line_on[product, month]
        )

    model.production_limit = pyo.Constraint(
        model.products, model.months, rule=production_limit_rule
    )

    def minimum_batch_rule(instance, product, month):
        return instance.production[product, month] >= (
            instance.minimum_batch[product] * instance.line_on[product, month]
        )

    model.batch_requirement = pyo.Constraint(
        model.products, model.months, rule=minimum_batch_rule
    )

    def inventory_balance_rule(instance, product, month):
        previous_inventory = (
            0 if month == 0 else instance.inventory[product, month - 1]
        )
        return instance.inventory[product, month] == (
            previous_inventory
            + instance.production[product, month]
            - instance.sales[product, month]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.months, rule=inventory_balance_rule
    )

    def storage_limit_rule(instance, month):
        return (
            sum(
                instance.inventory[product, month]
                for product in instance.products
            )
            <= instance.inventory_capacity
        )

    model.storage_limit = pyo.Constraint(
        model.months, rule=storage_limit_rule
    )

    model.net_revenue = pyo.Objective(
        expr=sum(
            model.unit_price[product] * model.sales[product, month]
            - model.unit_production_cost[product]
            * model.production[product, month]
            - model.line_activation_cost[product]
            * model.line_on[product, month]
            - model.unit_storage_cost[product]
            * model.inventory[product, month]
            for product in model.products
            for month in model.months
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Continue to objective retrieval only for the known no-solution error.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.net_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}