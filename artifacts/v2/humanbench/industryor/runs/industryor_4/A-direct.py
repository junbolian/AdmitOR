import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    candidates = ["A", "B", "C", "D", "E"]

    salary_A = params["salary_A"]
    salary_B = params["salary_B"]
    salary_C = params["salary_C"]
    salary_D = params["salary_D"]
    salary_E = params["salary_E"]
    max_hires = params["max_hires"]
    min_hires = params["min_hires"]
    budget = params["budget"]
    experience_A = params["experience_A"]
    experience_B = params["experience_B"]
    experience_C = params["experience_C"]
    experience_D = params["experience_D"]
    experience_E = params["experience_E"]
    min_experience = params["min_experience"]
    AE_max = params["AE_max"]
    min_advanced_degree = params["min_advanced_degree"]

    salaries = {
        "A": salary_A,
        "B": salary_B,
        "C": salary_C,
        "D": salary_D,
        "E": salary_E,
    }
    experiences = {
        "A": experience_A,
        "B": experience_B,
        "C": experience_C,
        "D": experience_D,
        "E": experience_E,
    }
    advanced_degree = {"B", "C"}

    model = pyo.ConcreteModel()

    model.hire = pyo.Var(candidates, domain=pyo.Binary)

    model.total_cost = pyo.Objective(
        expr=sum(salaries[c] * model.hire[c] for c in candidates),
        sense=pyo.minimize,
    )

    model.max_hires_con = pyo.Constraint(
        expr=sum(model.hire[c] for c in candidates) <= max_hires
    )
    model.min_hires_con = pyo.Constraint(
        expr=sum(model.hire[c] for c in candidates) >= min_hires
    )
    model.budget_con = pyo.Constraint(
        expr=sum(salaries[c] * model.hire[c] for c in candidates) <= budget
    )
    model.experience_con = pyo.Constraint(
        expr=sum(experiences[c] * model.hire[c] for c in candidates) >= min_experience
    )
    model.ae_con = pyo.Constraint(
        expr=model.hire["A"] + model.hire["E"] <= AE_max
    )
    model.advanced_con = pyo.Constraint(
        expr=sum(model.hire[c] for c in advanced_degree) >= min_advanced_degree
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}