# IR: {"sets":{"shipments":[0,1,2,3,4,5,6,7,8]},"params":{"value[i]":"params['value_'+str(i)] for i in shipments","weight[i]":"params['weight_'+str(i)] for i in shipments","capacity":"params['capacity']"},"variables":{"selected[i]":"Binary for i in shipments"},"constraints":["sum(weight[i]*selected[i] for i in shipments) <= capacity"],"objective":"maximize sum(value[i]*selected[i] for i in shipments)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.shipments = pyo.RangeSet(0, 8)

    model.shipment_value = pyo.Param(
        model.shipments,
        initialize={
            shipment: params[f"value_{shipment}"]
            for shipment in model.shipments
        },
    )
    model.shipment_weight = pyo.Param(
        model.shipments,
        initialize={
            shipment: params[f"weight_{shipment}"]
            for shipment in model.shipments
        },
    )
    model.cargo_capacity = pyo.Param(initialize=params["capacity"])

    model.selected = pyo.Var(model.shipments, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        expr=sum(
            model.shipment_weight[shipment] * model.selected[shipment]
            for shipment in model.shipments
        ) <= model.cargo_capacity
    )

    model.total_value = pyo.Objective(
        expr=sum(
            model.shipment_value[shipment] * model.selected[shipment]
            for shipment in model.shipments
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and must propagate.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}