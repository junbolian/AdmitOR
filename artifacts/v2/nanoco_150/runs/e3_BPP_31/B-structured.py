# IR: {"sets":{"VM":"0..15","SERVER":"0..15"},"params":{"vm_demands":"params['vm_demands'], indexed by VM","server_capacity":"params['server_capacity']"},"variables":{"assignment[VM,SERVER]":"binary","powered_on[SERVER]":"binary"},"constraints":["For each VM i: sum_j assignment[i,j] = 1","For each SERVER j: sum_i vm_demands[i]*assignment[i,j] <= server_capacity*powered_on[j]","For each VM i and SERVER j: assignment[i,j] <= powered_on[j]"],"objective":"minimize sum_j powered_on[j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vm_demands = params["vm_demands"]
    server_capacity = params["server_capacity"]

    if len(vm_demands) != 16:
        raise ValueError("vm_demands must contain exactly 16 resource demands.")

    model = pyo.ConcreteModel()

    # Sixteen candidate servers suffice: one per virtual machine.
    model.VM = pyo.RangeSet(0, 15)
    model.SERVER = pyo.RangeSet(0, 15)

    model.vm_demands = pyo.Param(
        model.VM,
        initialize={vm: vm_demands[vm] for vm in range(16)},
        within=pyo.NonNegativeReals,
    )
    model.server_capacity = pyo.Param(
        initialize=server_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.VM, model.SERVER, domain=pyo.Binary
    )
    model.powered_on = pyo.Var(model.SERVER, domain=pyo.Binary)

    def assignment_rule(instance, vm):
        return sum(
            instance.assignment[vm, server]
            for server in instance.SERVER
        ) == 1

    model.assign_once = pyo.Constraint(
        model.VM, rule=assignment_rule
    )

    def capacity_rule(instance, server):
        return sum(
            instance.vm_demands[vm] * instance.assignment[vm, server]
            for vm in instance.VM
        ) <= instance.server_capacity * instance.powered_on[server]

    model.capacity_limit = pyo.Constraint(
        model.SERVER, rule=capacity_rule
    )

    def powered_on_rule(instance, vm, server):
        return (
            instance.assignment[vm, server]
            <= instance.powered_on[server]
        )

    model.requires_power = pyo.Constraint(
        model.VM, model.SERVER, rule=powered_on_rule
    )

    model.total_powered_on = pyo.Objective(
        expr=sum(
            model.powered_on[server] for server in model.SERVER
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_powered_on))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}