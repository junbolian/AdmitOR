# IR: {"sets":{"VM":"1..10","SERVER":"1..10"},"params":{"cpu_capacity":"nonnegative scalar from params","mem_capacity":"nonnegative scalar from params","cpu_demand":"nonnegative vector from params indexed by VM","mem_demand":"nonnegative vector from params indexed by VM"},"variables":{"assigned[VM,SERVER]":"binary","server_on[SERVER]":"binary"},"constraints":["For each VM i: sum_s assigned[i,s] = 1","For each server s: sum_i cpu_demand[i]*assigned[i,s] <= cpu_capacity*server_on[s]","For each server s: sum_i mem_demand[i]*assigned[i,s] <= mem_capacity*server_on[s]","For each VM i and server s: assigned[i,s] <= server_on[s]"],"objective":"minimize sum_s server_on[s]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve VM placement with demands supplied as sequences or mappings.

    Sequences use VM order. Mapping keys may be integers 1..10,
    strings "1".."10", or strings "VM1".."VM10".
    """
    cpu_capacity = params["cpu_capacity"]
    mem_capacity = params["mem_capacity"]
    cpu_input = params["cpu_demand"]
    mem_input = params["mem_demand"]

    def demand_value(values, vm):
        if isinstance(values, Mapping):
            for key in (vm, str(vm), f"VM{vm}"):
                if key in values:
                    return values[key]
            raise KeyError(f"Missing demand for VM{vm}")
        return values[vm - 1]

    model = pyo.ConcreteModel()
    model.vm_set = pyo.RangeSet(1, 10)
    model.server_set = pyo.RangeSet(1, 10)

    model.cpu_capacity = pyo.Param(
        initialize=cpu_capacity,
        within=pyo.NonNegativeReals,
    )
    model.mem_capacity = pyo.Param(
        initialize=mem_capacity,
        within=pyo.NonNegativeReals,
    )
    model.cpu_demand = pyo.Param(
        model.vm_set,
        initialize={
            vm: demand_value(cpu_input, vm) for vm in model.vm_set
        },
        within=pyo.NonNegativeReals,
    )
    model.mem_demand = pyo.Param(
        model.vm_set,
        initialize={
            vm: demand_value(mem_input, vm) for vm in model.vm_set
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.vm_set, model.server_set, domain=pyo.Binary
    )
    model.server_on = pyo.Var(model.server_set, domain=pyo.Binary)

    def placement_rule(mod, vm):
        return sum(
            mod.assigned[vm, server] for server in mod.server_set
        ) == 1

    model.placement_constraints = pyo.Constraint(
        model.vm_set, rule=placement_rule
    )

    def cpu_rule(mod, server):
        return sum(
            mod.cpu_demand[vm] * mod.assigned[vm, server]
            for vm in mod.vm_set
        ) <= mod.cpu_capacity * mod.server_on[server]

    model.cpu_constraints = pyo.Constraint(
        model.server_set, rule=cpu_rule
    )

    def memory_rule(mod, server):
        return sum(
            mod.mem_demand[vm] * mod.assigned[vm, server]
            for vm in mod.vm_set
        ) <= mod.mem_capacity * mod.server_on[server]

    model.memory_constraints = pyo.Constraint(
        model.server_set, rule=memory_rule
    )

    def activation_rule(mod, vm, server):
        return mod.assigned[vm, server] <= mod.server_on[server]

    model.activation_constraints = pyo.Constraint(
        model.vm_set, model.server_set, rule=activation_rule
    )

    model.total_active = pyo.Objective(
        expr=sum(
            model.server_on[server] for server in model.server_set
        ),
        sense=pyo.minimize,
    )

    # Appsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_active))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}