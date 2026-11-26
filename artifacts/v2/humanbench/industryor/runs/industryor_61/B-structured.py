# IR: {"sets":{"workshops":["A","B","C","D"],"components":[1,2,3]},"params":{"capacity_A":"hours","capacity_B":"hours","capacity_C":"hours","capacity_D":"hours","productivity_A":"units/hour vector for components 1,2,3","productivity_B":"units/hour vector for components 1,2,3","productivity_C":"units/hour vector for components 1,2,3","productivity_D":"units/hour vector for components 1,2,3"},"variables":{"hours[w,c]":"nonnegative continuous","products":"nonnegative continuous"},"constraints":["For each workshop w: sum_c hours[w,c] <= capacity_w","For each component c: sum_w productivity_w[c] * hours[w,c] >= products"],"objective":"maximize products"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Maximize complete products, requiring one unit of each component.

    Each productivity parameter is a sequence ordered by components 1, 2, 3.
    Production hours and completed-product quantities are continuous.
    """
    capacity_data = {
        "A": params["capacity_A"],
        "B": params["capacity_B"],
        "C": params["capacity_C"],
        "D": params["capacity_D"],
    }
    productivity_data = {
        "A": params["productivity_A"],
        "B": params["productivity_B"],
        "C": params["productivity_C"],
        "D": params["productivity_D"],
    }

    model = pyo.ConcreteModel()
    model.workshops = pyo.Set(initialize=["A", "B", "C", "D"], ordered=True)
    model.components = pyo.Set(initialize=[1, 2, 3], ordered=True)

    model.capacity = pyo.Param(
        model.workshops,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.productivity = pyo.Param(
        model.workshops,
        model.components,
        initialize={
            (workshop, component): productivity_data[workshop][component - 1]
            for workshop in model.workshops
            for component in model.components
        },
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.workshops,
        model.components,
        domain=pyo.NonNegativeReals,
    )
    model.products = pyo.Var(domain=pyo.NonNegativeReals)

    def workshop_capacity_rule(instance, workshop):
        return (
            sum(
                instance.hours[workshop, component]
                for component in instance.components
            )
            <= instance.capacity[workshop]
        )

    model.workshop_capacity = pyo.Constraint(
        model.workshops,
        rule=workshop_capacity_rule,
    )

    def component_supply_rule(instance, component):
        return (
            sum(
                instance.productivity[workshop, component]
                * instance.hours[workshop, component]
                for workshop in instance.workshops
            )
            >= instance.products
        )

    model.component_supply = pyo.Constraint(
        model.components,
        rule=component_supply_rule,
    )

    model.total_products = pyo.Objective(
        expr=model.products,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_products))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}