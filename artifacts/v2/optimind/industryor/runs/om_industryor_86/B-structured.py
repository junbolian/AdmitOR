# IR: {"sets":{"products":["liquid","solid"],"machines":["machine1","machine2"]},"params":["machine1_time_liquid","machine2_time_liquid","machine1_time_solid","machine2_time_solid","initial_inventory_liquid","initial_inventory_solid","machine1_capacity_hours","machine2_capacity_hours","demand_liquid","demand_solid"],"variables":{"production[product]":"nonnegative integer","ending_inventory[product]":"nonnegative real"},"constraints":["For each machine: sum(time_minutes[machine,product]*production[product]) <= 60*capacity_hours[machine].","For each product: ending_inventory[product] = initial_inventory[product] + production[product] - demand[product]."],"objective":"Maximize sum(ending_inventory[product])."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=["liquid", "solid"], ordered=True)
    model.machines = pyo.Set(initialize=["machine1", "machine2"], ordered=True)

    model.time_minutes = pyo.Param(
        model.machines,
        model.products,
        initialize={
            ("machine1", "liquid"): params["machine1_time_liquid"],
            ("machine2", "liquid"): params["machine2_time_liquid"],
            ("machine1", "solid"): params["machine1_time_solid"],
            ("machine2", "solid"): params["machine2_time_solid"],
        },
        within=pyo.NonNegativeReals,
    )
    model.initial_inventory = pyo.Param(
        model.products,
        initialize={
            "liquid": params["initial_inventory_liquid"],
            "solid": params["initial_inventory_solid"],
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity_hours = pyo.Param(
        model.machines,
        initialize={
            "machine1": params["machine1_capacity_hours"],
            "machine2": params["machine2_capacity_hours"],
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.products,
        initialize={
            "liquid": params["demand_liquid"],
            "solid": params["demand_solid"],
        },
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, domain=pyo.NonNegativeIntegers
    )
    model.ending_inventory = pyo.Var(
        model.products, domain=pyo.NonNegativeReals
    )

    def machine_capacity_rule(mdl, machine):
        # Convert available processing time from hours to minutes.
        return sum(
            mdl.time_minutes[machine, product] * mdl.production[product]
            for product in mdl.products
        ) <= 60 * mdl.capacity_hours[machine]

    model.machine_capacity = pyo.Constraint(
        model.machines, rule=machine_capacity_rule
    )

    def inventory_balance_rule(mdl, product):
        return mdl.ending_inventory[product] == (
            mdl.initial_inventory[product]
            + mdl.production[product]
            - mdl.demand[product]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, rule=inventory_balance_rule
    )

    model.total_ending_inventory = pyo.Objective(
        expr=sum(
            model.ending_inventory[product] for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_ending_inventory))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}