# IR: {"sets":{"U":"range(params['num_units'])","R":"range(params['num_rooms'])","K":[0,1]},"params":{"num_units":"positive integer; params['num_units']","num_rooms":"positive integer; params['num_rooms']","flow_matrix":"nonnegative real[U,U]; params['flow_matrix']","distance_matrix":"nonnegative integer[R,R]; params['distance_matrix']","room_coordinates":"real[R,K]; params['room_coordinates']; surveyed metadata; distances are authoritative"},"variables":{"x[U,R]":"binary; unit-to-room assignment","y[U,U,R,R]":"continuous in [0,1]; product x[i,r]*x[j,s]"},"constraints":["For each i: sum_r x[i,r] = 1","For each r: sum_i x[i,r] = 1","For each i,j,r,s: y[i,j,r,s] <= x[i,r]","For each i,j,r,s: y[i,j,r,s] <= x[j,s]","For each i,j,r,s: y[i,j,r,s] >= x[i,r] + x[j,s] - 1"],"objective":"minimize sum_{i,j in U; r,s in R} flow_matrix[i,j] * distance_matrix[r,s] * y[i,j,r,s]; count all ordered unit pairs"}
import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_units = operator.index(params["num_units"])
    num_rooms = operator.index(params["num_rooms"])
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    room_coordinates = params["room_coordinates"]

    model = pyo.ConcreteModel()

    model.num_units = pyo.Param(
        initialize=num_units, within=pyo.PositiveIntegers
    )
    model.num_rooms = pyo.Param(
        initialize=num_rooms, within=pyo.PositiveIntegers
    )

    model.U = pyo.Set(initialize=range(num_units), ordered=True)
    model.R = pyo.Set(initialize=range(num_rooms), ordered=True)
    model.K = pyo.Set(initialize=(0, 1), ordered=True)

    model.flow_matrix = pyo.Param(
        model.U,
        model.U,
        initialize=lambda mdl, unit_i, unit_j: flow_matrix[unit_i][unit_j],
        within=pyo.NonNegativeReals,
    )
    model.distance_matrix = pyo.Param(
        model.R,
        model.R,
        initialize=lambda mdl, room_r, room_s: distance_matrix[room_r][room_s],
        within=pyo.NonNegativeIntegers,
    )
    model.room_coordinates = pyo.Param(
        model.R,
        model.K,
        initialize=lambda mdl, room_r, axis: room_coordinates[room_r][axis],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.U, model.R, domain=pyo.Binary)
    model.y = pyo.Var(
        model.U, model.U, model.R, model.R, domain=pyo.UnitInterval
    )

    def unit_assignment_rule(mdl, unit_i):
        return sum(mdl.x[unit_i, room_r] for room_r in mdl.R) == 1

    model.unit_assignment = pyo.Constraint(
        model.U, rule=unit_assignment_rule
    )

    def room_occupancy_rule(mdl, room_r):
        return sum(mdl.x[unit_i, room_r] for unit_i in mdl.U) == 1

    model.room_occupancy = pyo.Constraint(
        model.R, rule=room_occupancy_rule
    )

    def product_first_upper_rule(mdl, unit_i, unit_j, room_r, room_s):
        return (
            mdl.y[unit_i, unit_j, room_r, room_s]
            <= mdl.x[unit_i, room_r]
        )

    def product_second_upper_rule(mdl, unit_i, unit_j, room_r, room_s):
        return (
            mdl.y[unit_i, unit_j, room_r, room_s]
            <= mdl.x[unit_j, room_s]
        )

    def product_lower_rule(mdl, unit_i, unit_j, room_r, room_s):
        return (
            mdl.y[unit_i, unit_j, room_r, room_s]
            >= mdl.x[unit_i, room_r] + mdl.x[unit_j, room_s] - 1
        )

    model.product_first_upper = pyo.Constraint(
        model.U, model.U, model.R, model.R,
        rule=product_first_upper_rule,
    )
    model.product_second_upper = pyo.Constraint(
        model.U, model.U, model.R, model.R,
        rule=product_second_upper_rule,
    )
    model.product_lower = pyo.Constraint(
        model.U, model.U, model.R, model.R,
        rule=product_lower_rule,
    )

    model.total_travel_cost = pyo.Objective(
        expr=sum(
            model.flow_matrix[unit_i, unit_j]
            * model.distance_matrix[room_r, room_s]
            * model.y[unit_i, unit_j, room_r, room_s]
            for unit_i in model.U
            for unit_j in model.U
            for room_r in model.R
            for room_s in model.R
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Continue to the objective-retrieval check; propagate unrelated errors.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_travel_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}