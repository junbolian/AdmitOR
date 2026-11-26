# IR: {"sets":{"products":[0,1,2],"devices":["A","B","C"]},"params":{"device_A_hours_per_unit":"length-3 sequence","device_B_hours_per_unit":"length-3 sequence","device_C_hours_per_unit":"length-3 sequence","capacity_A":"scalar","capacity_B":"scalar","capacity_C":"scalar","unit_profit":"length-3 sequence"},"variables":{"production[p]":"nonnegative continuous, p in products"},"constraints":["For each device d: sum(hours[d,p]*production[p] for p in products) <= capacity[d]"],"objective":"maximize sum(unit_profit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hours_by_device = {
        "A": params["device_A_hours_per_unit"],
        "B": params["device_B_hours_per_unit"],
        "C": params["device_C_hours_per_unit"],
    }
    capacities = {
        "A": params["capacity_A"],
        "B": params["capacity_B"],
        "C": params["capacity_C"],
    }
    profits = params["unit_profit"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.devices = pyo.Set(initialize=["A", "B", "C"], ordered=True)

    model.processing_hours = pyo.Param(
        model.devices,
        model.products,
        initialize={
            (device, product): hours_by_device[device][product]
            for device in model.devices
            for product in model.products
        },
    )
    model.device_capacity = pyo.Param(
        model.devices,
        initialize=capacities,
    )
    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={product: profits[product] for product in model.products},
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(instance, device):
        return sum(
            instance.processing_hours[device, product]
            * instance.production[product]
            for product in instance.products
        ) <= instance.device_capacity[device]

    model.capacity_limits = pyo.Constraint(
        model.devices,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}