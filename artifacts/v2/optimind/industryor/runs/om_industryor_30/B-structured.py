# IR: {"sets":{"W":["A","B","C","D"],"J":[1,2,3]},"params":{"capacity":"params['capacity']: hours for W in order","rate_A":"params['rate_A']: rates for J in order","rate_B":"params['rate_B']: rates for J in order","rate_C":"params['rate_C']: rates for J in order","rate_D":"params['rate_D']: rates for J in order"},"variables":{"hours[w,j]":"nonnegative continuous","products":"nonnegative continuous"},"constraints":["sum(hours[w,j] for j in J) <= capacity[w] for each w in W","sum(rate[w,j]*hours[w,j] for w in W) >= products for each j in J"],"objective":"maximize products"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the continuous production-allocation model.

    Inputs are sequences: capacity follows A, B, C, D; each rate
    sequence follows components 1, 2, 3. Each product requires one
    unit of each component.
    """
    workshops = ("A", "B", "C", "D")
    components = (1, 2, 3)

    capacity_data = params["capacity"]
    rate_data = {
        "A": params["rate_A"],
        "B": params["rate_B"],
        "C": params["rate_C"],
        "D": params["rate_D"],
    }

    model = pyo.ConcreteModel()

    model.workshops = pyo.Set(initialize=workshops, ordered=True)
    model.components = pyo.Set(initialize=components, ordered=True)

    model.capacity_hours = pyo.Param(
        model.workshops,
        initialize={
            workshop: capacity_data[position]
            for position, workshop in enumerate(workshops)
        },
        within=pyo.NonNegativeReals,
    )
    model.production_rate = pyo.Param(
        model.workshops,
        model.components,
        initialize={
            (workshop, component): rate_data[workshop][position]
            for workshop in workshops
            for position, component in enumerate(components)
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
            <= instance.capacity_hours[workshop]
        )

    model.workshop_capacity = pyo.Constraint(
        model.workshops, rule=workshop_capacity_rule
    )

    def component_supply_rule(instance, component):
        return (
            sum(
                instance.production_rate[workshop, component]
                * instance.hours[workshop, component]
                for workshop in instance.workshops
            )
            >= instance.products
        )

    model.component_supply = pyo.Constraint(
        model.components, rule=component_supply_rule
    )

    model.total_products = pyo.Objective(
        expr=model.products, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_products))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}