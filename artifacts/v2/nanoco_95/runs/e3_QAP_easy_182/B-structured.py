# IR: {"sets":{"F":"range(num_facilities)","L":"range(num_locations)","Q":"{(i,j,k,l): i,j in F, i!=j, k,l in L, k!=l}"},"params":{"num_facilities":"params['num_facilities']","num_locations":"params['num_locations']","flow_matrix":"params['flow_matrix'], flat row-major F x F","distance_matrix":"params['distance_matrix'], flat row-major L x L"},"variables":{"x[i,k]":"binary, i in F, k in L","y[i,j,k,l]":"continuous [0,1], (i,j,k,l) in Q"},"constraints":["sum(k in L) x[i,k] = 1 for each i in F","sum(i in F) x[i,k] = 1 for each k in L","y[i,j,k,l] <= x[i,k] for each (i,j,k,l) in Q","y[i,j,k,l] <= x[j,l] for each (i,j,k,l) in Q","y[i,j,k,l] >= x[i,k] + x[j,l] - 1 for each (i,j,k,l) in Q"],"objective":"minimize sum((i,j,k,l) in Q) flow_matrix[i*num_facilities+j]*distance_matrix[k*num_locations+l]*y[i,j,k,l]; counts all ordered rack pairs"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_facilities = params["num_facilities"]
    num_locations = params["num_locations"]
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(
        initialize=range(num_facilities),
        ordered=True,
    )
    model.L = pyo.Set(
        initialize=range(num_locations),
        ordered=True,
    )
    model.Q = pyo.Set(
        dimen=4,
        initialize=(
            (rack_i, rack_j, slot_k, slot_l)
            for rack_i in range(num_facilities)
            for rack_j in range(num_facilities)
            for slot_k in range(num_locations)
            for slot_l in range(num_locations)
            if rack_i != rack_j and slot_k != slot_l
        ),
        ordered=True,
    )

    model.flow = pyo.Param(
        model.F,
        model.F,
        initialize={
            (rack_i, rack_j):
                flow_matrix[rack_i * num_facilities + rack_j]
            for rack_i in range(num_facilities)
            for rack_j in range(num_facilities)
        },
    )
    model.distance = pyo.Param(
        model.L,
        model.L,
        initialize={
            (slot_k, slot_l):
                distance_matrix[slot_k * num_locations + slot_l]
            for slot_k in range(num_locations)
            for slot_l in range(num_locations)
        },
    )

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)
    model.y = pyo.Var(model.Q, domain=pyo.UnitInterval)

    def rack_assignment_rule(instance, rack_i):
        return sum(
            instance.x[rack_i, slot_k] for slot_k in instance.L
        ) == 1

    model.rack_assignment = pyo.Constraint(
        model.F,
        rule=rack_assignment_rule,
    )

    def slot_assignment_rule(instance, slot_k):
        return sum(
            instance.x[rack_i, slot_k] for rack_i in instance.F
        ) == 1

    model.slot_assignment = pyo.Constraint(
        model.L,
        rule=slot_assignment_rule,
    )

    def product_upper_first_rule(instance, rack_i, rack_j, slot_k, slot_l):
        return (
            instance.y[rack_i, rack_j, slot_k, slot_l]
            <= instance.x[rack_i, slot_k]
        )

    model.product_upper_first = pyo.Constraint(
        model.Q,
        rule=product_upper_first_rule,
    )

    def product_upper_second_rule(instance, rack_i, rack_j, slot_k, slot_l):
        return (
            instance.y[rack_i, rack_j, slot_k, slot_l]
            <= instance.x[rack_j, slot_l]
        )

    model.product_upper_second = pyo.Constraint(
        model.Q,
        rule=product_upper_second_rule,
    )

    def product_lower_rule(instance, rack_i, rack_j, slot_k, slot_l):
        return (
            instance.y[rack_i, rack_j, slot_k, slot_l]
            >= instance.x[rack_i, slot_k] + instance.x[rack_j, slot_l] - 1
        )

    model.product_lower = pyo.Constraint(
        model.Q,
        rule=product_lower_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.flow[rack_i, rack_j]
            * model.distance[slot_k, slot_l]
            * model.y[rack_i, rack_j, slot_k, slot_l]
            for rack_i, rack_j, slot_k, slot_l in model.Q
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}