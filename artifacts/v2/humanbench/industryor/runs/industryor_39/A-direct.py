import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    model = pyo.ConcreteModel()

    chicken = params["protein_chicken"]
    salmon = params["protein_salmon"]
    tofu = params["protein_tofu"]
    p_chicken = params["price_chicken"]
    p_salmon = params["price_salmon"]
    p_tofu = params["price_tofu"]
    budget = params["budget"]
    max_weight = params["max_weight"]

    veg = ["v1", "v2", "v3", "v4", "v5"]
    prot = ["chicken", "salmon", "tofu"]

    model.Veg = pyo.Set(initialize=veg)
    model.Prot = pyo.Set(initialize=prot)

    model.x_veg = pyo.Var(model.Veg, domain=pyo.NonNegativeReals)
    model.x_prot = pyo.Var(model.Prot, domain=pyo.NonNegativeReals)
    model.y_veg = pyo.Var(model.Veg, domain=pyo.Binary)
    model.y_prot = pyo.Var(model.Prot, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=chicken * model.x_prot["chicken"]
        + salmon * model.x_prot["salmon"]
        + tofu * model.x_prot["tofu"],
        sense=pyo.maximize,
    )

    model.budget_con = pyo.Constraint(
        expr=p_chicken * model.x_prot["chicken"]
        + p_salmon * model.x_prot["salmon"]
        + p_tofu * model.x_prot["tofu"]
        <= budget
    )

    model.weight_con = pyo.Constraint(
        expr=sum(model.x_veg[v] for v in model.Veg)
        + sum(model.x_prot[p] for p in model.Prot)
        <= max_weight
    )

    model.veg_type_con = pyo.Constraint(
        expr=sum(model.y_veg[v] for v in model.Veg) >= 3
    )

    model.prot_type_con = pyo.Constraint(
        expr=sum(model.y_prot[p] for p in model.Prot) == 1
    )

    model.veg_link = pyo.Constraint(
        model.Veg, rule=lambda m, v: m.x_veg[v] <= max_weight * m.y_veg[v]
    )
    model.prot_link = pyo.Constraint(
        model.Prot, rule=lambda m, p: m.x_prot[p] <= max_weight * m.y_prot[p]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}