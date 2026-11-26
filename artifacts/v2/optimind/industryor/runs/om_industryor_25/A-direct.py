import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    products = ['I', 'II', 'III']
    machines_A = ['A1', 'A2']
    machines_B = ['B1', 'B2', 'B3']
    all_machines = machines_A + machines_B

    # Feasible machine-product assignments (process A)
    assign_A = {
        'I': ['A1', 'A2'],
        'II': ['A1', 'A2'],
        'III': ['A2'],
    }
    # Feasible machine-product assignments (process B)
    assign_B = {
        'I': ['B1', 'B2', 'B3'],
        'II': ['B1'],
        'III': ['B2'],
    }

    # Processing times read from params, stored as dicts keyed by machine
    pt_I = params["processing_time_I"]
    pt_II = params["processing_time_II"]
    pt_III = params["processing_time_III"]
    proc = {
        'I': pt_I,
        'II': pt_II,
        'III': pt_III,
    }

    eff_hours = params["effective_hours"]
    op_cost = params["operating_cost_full"]
    raw_cost = params["raw_material_cost"]
    price = params["unit_price"]

    model = pyo.ConcreteModel()

    # Total production quantity per product
    model.qty = pyo.Var(products, domain=pyo.NonNegativeReals)

    # Process-A allocation variable: xA[product, machine]
    xA_index = [(p, mk) for p in products for mk in assign_A[p]]
    model.xA = pyo.Var(xA_index, domain=pyo.NonNegativeReals)

    # Process-B allocation variable: xB[product, machine]
    xB_index = [(p, mk) for p in products for mk in assign_B[p]]
    model.xB = pyo.Var(xB_index, domain=pyo.NonNegativeReals)

    # Flow balance for process A: sum over A machines = qty
    def flow_A_rule(model, p):
        return sum(model.xA[p, mk] for mk in assign_A[p]) == model.qty[p]
    model.flow_A = pyo.Constraint(products, rule=flow_A_rule)

    # Flow balance for process B: sum over B machines = qty
    def flow_B_rule(model, p):
        return sum(model.xB[p, mk] for mk in assign_B[p]) == model.qty[p]
    model.flow_B = pyo.Constraint(products, rule=flow_B_rule)

    # Machine capacity (effective hours) constraints
    def cap_A_rule(model, mk):
        return sum(model.xA[p, mk] * proc[p][mk] for p in products
                   if mk in assign_A[p]) <= eff_hours[mk]
    model.cap_A = pyo.Constraint(machines_A, rule=cap_A_rule)

    def cap_B_rule(model, mk):
        return sum(model.xB[p, mk] * proc[p][mk] for p in products
                   if mk in assign_B[p]) <= eff_hours[mk]
    model.cap_B = pyo.Constraint(machines_B, rule=cap_B_rule)

    # Objective: maximize total profit
    # Revenue minus raw material cost minus operating costs
    revenue = sum(price[p] * model.qty[p] for p in products)
    material = sum(raw_cost[p] * model.qty[p] for p in products)
    operating = sum(op_cost[mk] for mk in all_machines)

    model.obj = pyo.Objective(
        expr=revenue - material - operating,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}