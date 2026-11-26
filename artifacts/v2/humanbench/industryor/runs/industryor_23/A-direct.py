import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hours_A = params["device_A_hours_per_unit"]
    hours_B = params["device_B_hours_per_unit"]
    hours_C = params["device_C_hours_per_unit"]
    cap_A = params["capacity_A"]
    cap_B = params["capacity_B"]
    cap_C = params["capacity_C"]
    profit = params["unit_profit"]

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[0, 1, 2])

    model.x = pyo.Var(model.products, bounds=(0, None))

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.products)

    model.profit_obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_A_rule(m):
        return sum(hours_A[i] * m.x[i] for i in m.products) <= cap_A

    def cap_B_rule(m):
        return sum(hours_B[i] * m.x[i] for i in m.products) <= cap_B

    def cap_C_rule(m):
        return sum(hours_C[i] * m.x[i] for i in m.products) <= cap_C

    model.cap_A = pyo.Constraint(rule=cap_A_rule)
    model.cap_B = pyo.Constraint(rule=cap_B_rule)
    model.cap_C = pyo.Constraint(rule=cap_C_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.profit_obj))
    return {"objective": obj_val, "status": "optimal"}