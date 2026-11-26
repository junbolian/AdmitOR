# IR: {"sets":{"products":[1,2,3],"positions":[1,2,3],"machines":[1,2,3]},"params":{"t_11":"processing time (1,1)","t_12":"processing time (1,2)","t_13":"processing time (1,3)","t_21":"processing time (2,1)","t_22":"processing time (2,2)","t_23":"processing time (2,3)","t_31":"processing time (3,1)","t_32":"processing time (3,2)","t_33":"processing time (3,3)"},"variables":{"x[i,k]":"binary; product i occupies position k on every machine","s[k,j]":"nonnegative continuous; start time of position k on machine j"},"expressions":{"d[k,j]":"sum_i t[i,j]*x[i,k]"},"constraints":["For each product i: sum_k x[i,k] = 1","For each position k: sum_i x[i,k] = 1","For each position k and machine j < 3: s[k,j+1] >= s[k,j] + d[k,j]","For each position k < 3 and machine j: s[k+1,j] >= s[k,j] + d[k,j]"],"objective":"minimize s[3,3] + d[3,3]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        (1, 1): params["t_11"],
        (1, 2): params["t_12"],
        (1, 3): params["t_13"],
        (2, 1): params["t_21"],
        (2, 2): params["t_22"],
        (2, 3): params["t_23"],
        (3, 1): params["t_31"],
        (3, 2): params["t_32"],
        (3, 3): params["t_33"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(1, 3)
    model.positions = pyo.RangeSet(1, 3)
    model.machines = pyo.RangeSet(1, 3)

    model.processing_time = pyo.Param(
        model.products,
        model.machines,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.products, model.positions, domain=pyo.Binary
    )
    model.s = pyo.Var(
        model.positions, model.machines, domain=pyo.NonNegativeReals
    )

    def duration_rule(model, position, machine):
        return sum(
            model.processing_time[product, machine]
            * model.x[product, position]
            for product in model.products
        )

    model.duration = pyo.Expression(
        model.positions, model.machines, rule=duration_rule
    )

    def product_assignment_rule(model, product):
        return sum(
            model.x[product, position] for position in model.positions
        ) == 1

    model.product_assignment = pyo.Constraint(
        model.products, rule=product_assignment_rule
    )

    def position_assignment_rule(model, position):
        return sum(
            model.x[product, position] for product in model.products
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions, rule=position_assignment_rule
    )

    def product_flow_rule(model, position, machine):
        if machine == 3:
            return pyo.Constraint.Skip
        return (
            model.s[position, machine + 1]
            >= model.s[position, machine] + model.duration[position, machine]
        )

    model.product_flow = pyo.Constraint(
        model.positions, model.machines, rule=product_flow_rule
    )

    def machine_capacity_rule(model, position, machine):
        if position == 3:
            return pyo.Constraint.Skip
        return (
            model.s[position + 1, machine]
            >= model.s[position, machine] + model.duration[position, machine]
        )

    model.machine_capacity = pyo.Constraint(
        model.positions, model.machines, rule=machine_capacity_rule
    )

    model.total_cycle = pyo.Objective(
        expr=model.s[3, 3] + model.duration[3, 3],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cycle))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}