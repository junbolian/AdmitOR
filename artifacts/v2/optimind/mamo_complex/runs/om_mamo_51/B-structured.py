# IR: {"sets":{},"params":["machine_hours_available","machine_hours_per_unit_product1","machine_hours_per_unit_product2","production_cost_product1","production_cost_product2","selling_price_product1","selling_price_product2","cash_available","finance_fraction_product1","finance_fraction_product2","extra_machine_hours","repair_cost"],"variables":{"x1":"NonNegativeReals","x2":"NonNegativeReals","repair":"Binary"},"constraints":{"machine_capacity":"machine_hours_per_unit_product1*x1 + machine_hours_per_unit_product2*x2 <= machine_hours_available + extra_machine_hours*repair","cash_financing":"production_cost_product1*x1 + production_cost_product2*x2 + repair_cost*repair <= cash_available + finance_fraction_product1*selling_price_product1*x1 + finance_fraction_product2*selling_price_product2*x2"},"objective":{"sense":"maximize","expression":"(selling_price_product1-production_cost_product1)*x1 + (selling_price_product2-production_cost_product2)*x2 - repair_cost*repair"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.machine_hours_available = pyo.Param(
        initialize=params["machine_hours_available"]
    )
    model.machine_hours_per_unit_product1 = pyo.Param(
        initialize=params["machine_hours_per_unit_product1"]
    )
    model.machine_hours_per_unit_product2 = pyo.Param(
        initialize=params["machine_hours_per_unit_product2"]
    )
    model.production_cost_product1 = pyo.Param(
        initialize=params["production_cost_product1"]
    )
    model.production_cost_product2 = pyo.Param(
        initialize=params["production_cost_product2"]
    )
    model.selling_price_product1 = pyo.Param(
        initialize=params["selling_price_product1"]
    )
    model.selling_price_product2 = pyo.Param(
        initialize=params["selling_price_product2"]
    )
    model.cash_available = pyo.Param(
        initialize=params["cash_available"]
    )
    model.finance_fraction_product1 = pyo.Param(
        initialize=params["finance_fraction_product1"]
    )
    model.finance_fraction_product2 = pyo.Param(
        initialize=params["finance_fraction_product2"]
    )
    model.extra_machine_hours = pyo.Param(
        initialize=params["extra_machine_hours"]
    )
    model.repair_cost = pyo.Param(
        initialize=params["repair_cost"]
    )

    # Production quantities are continuous; the repair decision is binary.
    model.x1 = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2 = pyo.Var(domain=pyo.NonNegativeReals)
    model.repair = pyo.Var(domain=pyo.Binary)

    model.machine_capacity = pyo.Constraint(
        expr=(
            model.machine_hours_per_unit_product1 * model.x1
            + model.machine_hours_per_unit_product2 * model.x2
            <= model.machine_hours_available
            + model.extra_machine_hours * model.repair
        )
    )

    model.cash_financing = pyo.Constraint(
        expr=(
            model.production_cost_product1 * model.x1
            + model.production_cost_product2 * model.x2
            + model.repair_cost * model.repair
            <= model.cash_available
            + model.finance_fraction_product1
            * model.selling_price_product1
            * model.x1
            + model.finance_fraction_product2
            * model.selling_price_product2
            * model.x2
        )
    )

    model.net_income = pyo.Objective(
        expr=(
            (model.selling_price_product1 - model.production_cost_product1)
            * model.x1
            + (model.selling_price_product2 - model.production_cost_product2)
            * model.x2
            - model.repair_cost * model.repair
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this specific error when no solution can be loaded.
        # Other runtime errors are unexpected and must propagate.
        if "A feasible solution was not found" in str(error):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.net_income))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}