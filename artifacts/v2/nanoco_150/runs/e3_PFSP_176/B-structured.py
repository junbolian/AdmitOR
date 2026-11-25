# IR: {"sets":{"V":"range(params['num_vehicles'])","K":"range(params['num_vehicles'])","W":"range(params['num_workstations'])"},"params":{"num_vehicles":"positive integer, frozen","num_workstations":"positive integer, frozen","processing_times":"nonnegative matrix indexed by V,W"},"variables":{"x[v,k]":"binary; vehicle v occupies sequence position k","C[k,w]":"nonnegative continuous; completion time at position k on workstation w"},"expressions":{"D[k,w]":"sum(processing_times[v][w]*x[v,k] for v in V)"},"constraints":["Each vehicle occupies exactly one position: sum(x[v,k] for k in K)=1 for each v.","Each position contains exactly one vehicle: sum(x[v,k] for v in V)=1 for each k.","Workstation capacity: C[k,w]>=(C[k-1,w] if k>0 else 0)+D[k,w] for each k,w.","Vehicle routing: C[k,w]>=(C[k,w-1] if w>0 else 0)+D[k,w] for each k,w."],"objective":"minimize C[num_vehicles-1,num_workstations-1]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_vehicles = params["num_vehicles"]
    num_workstations = params["num_workstations"]
    processing_times = params["processing_times"]

    model = pyo.ConcreteModel()

    model.vehicles = pyo.RangeSet(0, num_vehicles - 1)
    model.positions = pyo.RangeSet(0, num_vehicles - 1)
    model.workstations = pyo.RangeSet(0, num_workstations - 1)

    model.processing_duration = pyo.Param(
        model.vehicles,
        model.workstations,
        initialize=lambda mdl, vehicle, station: processing_times[vehicle][station],
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.vehicles,
        model.positions,
        domain=pyo.Binary,
    )
    model.completion_time = pyo.Var(
        model.positions,
        model.workstations,
        domain=pyo.NonNegativeReals,
    )

    def position_duration_rule(mdl, position, station):
        return sum(
            mdl.processing_duration[vehicle, station]
            * mdl.assignment[vehicle, position]
            for vehicle in mdl.vehicles
        )

    model.position_duration = pyo.Expression(
        model.positions,
        model.workstations,
        rule=position_duration_rule,
    )

    def vehicle_assignment_rule(mdl, vehicle):
        return sum(
            mdl.assignment[vehicle, position] for position in mdl.positions
        ) == 1

    model.vehicle_assignment = pyo.Constraint(
        model.vehicles,
        rule=vehicle_assignment_rule,
    )

    def position_assignment_rule(mdl, position):
        return sum(
            mdl.assignment[vehicle, position] for vehicle in mdl.vehicles
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=position_assignment_rule,
    )

    def workstation_capacity_rule(mdl, position, station):
        previous_completion = (
            mdl.completion_time[position - 1, station] if position > 0 else 0
        )
        return (
            mdl.completion_time[position, station]
            >= previous_completion + mdl.position_duration[position, station]
        )

    model.workstation_capacity = pyo.Constraint(
        model.positions,
        model.workstations,
        rule=workstation_capacity_rule,
    )

    def vehicle_routing_rule(mdl, position, station):
        previous_completion = (
            mdl.completion_time[position, station - 1] if station > 0 else 0
        )
        return (
            mdl.completion_time[position, station]
            >= previous_completion + mdl.position_duration[position, station]
        )

    model.vehicle_routing = pyo.Constraint(
        model.positions,
        model.workstations,
        rule=vehicle_routing_rule,
    )

    model.total_completion_time = pyo.Objective(
        expr=model.completion_time[num_vehicles - 1, num_workstations - 1],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion_time))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}