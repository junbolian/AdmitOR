# panel_base_3of3 certificates that miss the OptiMind answer

Every panel_base_3of3 certificate whose value misses the answer. OptiMind cleaned IndustryOR and Mamo-Complex (`datasets/optimind_corrected/SOURCE.md`), scored with `round_aware` of scripts/score_eval.py against the OptiMind answers. Sections: identification, problem text, extracted parameter set with warnings, the three programs, values on the stated and resampled instances (both samplers), and the data-verification replies of the three families.

| Sample id | Benchmark | Problem class | Certified value | Answer | B or C flags |
|---|---|---|---:|---:|---|
| `om_industryor_85` | OptiMind IndustryOR | ['Multi-Commodity Transportation Problem'] | 4500.0 | 4170 | yes |
| `om_industryor_89` | OptiMind IndustryOR | ['Profit Maximization Problem', 'Production Planning Problem'] | 409.09090909090907 | 408 | no |
| `om_mamo_27` | OptiMind Mamo-Complex | ['Diet Problem'] | 19.217560975609757 | 22 | no |
| `om_mamo_34` | OptiMind Mamo-Complex | ["TravelingSalesman"] | 198.0 | 192 | no |
| `om_mamo_77` | OptiMind Mamo-Complex | ['Capacitated Facility Location Problem'] | 749131.9999999995 | 749272 | yes |
| `om_mamo_103` | OptiMind Mamo-Complex | ['Capacitated Facility Location Problem'] | 589621.0 | 567010 | no |
| `om_mamo_114` | OptiMind Mamo-Complex | ['Capacitated Facility Location Problem'] | 588594.9999999998 | 58895 | no |
| `om_mamo_131` | OptiMind Mamo-Complex | ['Diet Problem'] | 148.61089494163426 | 178 | no |
| `om_mamo_194` | OptiMind Mamo-Complex | ["Facility Location Problem (FLP)"] | 66.3661 | 66.39 | no |
| `om_mamo_197` | OptiMind Mamo-Complex | ['Diet Problem'] | 38.0 | 24 | yes |
| `om_mamo_206` | OptiMind Mamo-Complex | ['Capacitated Facility Location Problem'] | 580131.0 | 610975 | no |

## 1. om_industryor_85 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_85` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 85) |
| Problem class (OptiMind) | ['Multi-Commodity Transportation Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 4500.0 |
| Answer (OptiMind) | 4170 |
| Rules that certify it | gate 4500.0, gate_3fam 4500.0, gate_tau 4500.0, panel_base_2of3 4500.0, panel_base_3of3 4500.0, ind_gate 4500.0, ind_gate_tau 4500.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any True (mismatch True, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch True, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
A transportation company has two types of trucks, Type A and Type B. Type A trucks have 20 cubic meters of refrigerated capacity and 40 cubic meters of non-refrigerated capacity. In contrast, Type B trucks have the same total capacity, but the capacities for refrigerated and non-refrigerated cargo are equal. A grocer needs to rent trucks to transport 3000 cubic meters of refrigerated cargo and 4000 cubic meters of non-refrigerated cargo. The rental cost per kilometer for Type A trucks is £30, while the rental cost per kilometer for Type B trucks is £40. How many of each type of truck should the grocer rent to minimize the total cost?

Try to formulate a model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"refrigerated_capacity_A": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"nonrefrigerated_capacity_A": {"base":40,"perturb":{"mode":"rel","r":0.5}}
"total_capacity_B": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"refrigerated_demand": {"base":3000,"perturb":{"mode":"rel","r":0.5}}
"nonrefrigerated_demand": {"base":4000,"perturb":{"mode":"rel","r":0.5}}
"cost_per_km_A": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"cost_per_km_B": {"base":40,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    ref_cap_A = params["refrigerated_capacity_A"]
    nonref_cap_A = params["nonrefrigerated_capacity_A"]
    total_cap_B = params["total_capacity_B"]
    ref_demand = params["refrigerated_demand"]
    nonref_demand = params["nonrefrigerated_demand"]
    cost_A = params["cost_per_km_A"]
    cost_B = params["cost_per_km_B"]

    # Type B splits total capacity equally between refrigerated and non-refrigerated
    ref_cap_B = total_cap_B / 2.0
    nonref_cap_B = total_cap_B / 2.0

    model = pyo.ConcreteModel()
    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.ref_constraint = pyo.Constraint(
        expr=ref_cap_A * model.xA + ref_cap_B * model.xB >= ref_demand
    )
    model.nonref_constraint = pyo.Constraint(
        expr=nonref_cap_A * model.xA + nonref_cap_B * model.xB >= nonref_demand
    )

    model.total_cost = pyo.Objective(
        expr=cost_A * model.xA + cost_B * model.xB, sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"truck_types":["A","B"],"cargo_types":["refrigerated","nonrefrigerated"]},"params":["refrigerated_capacity_A","nonrefrigerated_capacity_A","total_capacity_B","refrigerated_demand","nonrefrigerated_demand","cost_per_km_A","cost_per_km_B"],"variables":{"trucks_A":"nonnegative integer","trucks_B":"nonnegative integer"},"constraints":["refrigerated_capacity_A*trucks_A+(total_capacity_B/2)*trucks_B>=refrigerated_demand","nonrefrigerated_capacity_A*trucks_A+(total_capacity_B/2)*trucks_B>=nonrefrigerated_demand"],"objective":"minimize cost_per_km_A*trucks_A+cost_per_km_B*trucks_B"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    refrigerated_capacity_A = params["refrigerated_capacity_A"]
    nonrefrigerated_capacity_A = params["nonrefrigerated_capacity_A"]
    total_capacity_B = params["total_capacity_B"]
    refrigerated_demand = params["refrigerated_demand"]
    nonrefrigerated_demand = params["nonrefrigerated_demand"]
    cost_per_km_A = params["cost_per_km_A"]
    cost_per_km_B = params["cost_per_km_B"]

    model = pyo.ConcreteModel()

    model.trucks_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.trucks_B = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.refrigerated_requirement = pyo.Constraint(
        expr=(
            refrigerated_capacity_A * model.trucks_A
            + (total_capacity_B / 2) * model.trucks_B
            >= refrigerated_demand
        )
    )
    model.nonrefrigerated_requirement = pyo.Constraint(
        expr=(
            nonrefrigerated_capacity_A * model.trucks_A
            + (total_capacity_B / 2) * model.trucks_B
            >= nonrefrigerated_demand
        )
    )

    model.total_cost = pyo.Objective(
        expr=(
            cost_per_km_A * model.trucks_A
            + cost_per_km_B * model.trucks_B
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    ref_cap_A = params["refrigerated_capacity_A"]
    nonref_cap_A = params["nonrefrigerated_capacity_A"]
    total_cap_B = params["total_capacity_B"]
    ref_demand = params["refrigerated_demand"]
    nonref_demand = params["nonrefrigerated_demand"]
    cost_A = params["cost_per_km_A"]
    cost_B = params["cost_per_km_B"]

    # Type B splits total capacity equally between refrigerated and non-refrigerated
    ref_cap_B = total_cap_B / 2.0
    nonref_cap_B = total_cap_B / 2.0

    model = gp.Model("truck_rental")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of each truck type (integer)
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")

    # Objective: minimize total cost per km
    model.setObjective(cost_A * x_A + cost_B * x_B, GRB.MINIMIZE)

    # Constraints: meet refrigerated and non-refrigerated demands
    model.addConstr(ref_cap_A * x_A + ref_cap_B * x_B >= ref_demand, name="ref_demand")
    model.addConstr(nonref_cap_A * x_A + nonref_cap_B * x_B >= nonref_demand, name="nonref_demand")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 4500.0 (optimal) | 4500.0 (optimal) | 4500.0 (optimal) |
| 1 | 8331.032370954212 (optimal) | 8331.032370954212 (optimal) | 8331.032370954212 (optimal) |
| 2 | 2906.478552654927 (optimal) | 2906.478552654927 (optimal) | 2906.478552654927 (optimal) |
| 3 | 2172.8796790188817 (optimal) | 2172.8796790188817 (optimal) | 2172.8796790188817 (optimal) |
| 4 | 3254.1746801570116 (optimal) | 3254.1746801570116 (optimal) | 3254.1746801570116 (optimal) |
| 5 | 6054.505789955213 (optimal) | 6054.505789955213 (optimal) | 6054.505789955213 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 4500.0 (optimal) | 4500.0 (optimal) | 4500.0 (optimal) |
| 1 | 8331.032370954212 (optimal) | 8331.032370954212 (optimal) | 8331.032370954212 (optimal) |
| 2 | 2906.478552654927 (optimal) | 2906.478552654927 (optimal) | 2906.478552654927 (optimal) |
| 3 | 2172.8796790188817 (optimal) | 2172.8796790188817 (optimal) | 2172.8796790188817 (optimal) |
| 4 | 3254.1746801570116 (optimal) | 3254.1746801570116 (optimal) | 3254.1746801570116 (optimal) |
| 5 | 6054.505789955213 (optimal) | 6054.505789955213 (optimal) | 6054.505789955213 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "total_capacity_B",
      "extracted": 30,
      "stated": 60,
      "evidence": "Type B trucks have the same total capacity"
    }
  ],
  "not_stated": []
}
```
````

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

```json
{"mismatch":[{"parameter":"total_capacity_B","extracted":30,"stated":60,"evidence":"Type A trucks have 20 cubic meters of refrigerated capacity and 40 cubic meters of non-refrigerated capacity. In contrast, Type B trucks have the same total capacity"}],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 3; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "total_capacity_B",
      "extracted": 30,
      "stated": 60,
      "evidence": "Type A trucks have 20 cubic meters of refrigerated capacity and 40 cubic meters of non-refrigerated capacity... Type B trucks have the same total capacity"
    }
  ],
  "not_stated": []
}
```
````


## 2. om_industryor_89 (OptiMind IndustryOR)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_industryor_89` |
| Benchmark | OptiMind IndustryOR (`datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv`, 0-based row 89) |
| Problem class (OptiMind) | ['Profit Maximization Problem', 'Production Planning Problem'] |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 409.09090909090907 |
| Answer (OptiMind) | 408 |
| Rules that certify it | gate 409.09090909090907, gate_3fam 409.09090909090907, gate_tau 409.09090909090907, panel_base_2of3 409.09090909090907, panel_base_3of3 409.09090909090907, ind_gate 409.09090909090907, ind_gate_tau 409.09090909090907 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
A company produces two products (A and B), with a profit of £3 and £5 per unit sold, respectively. Each product must be assembled on a specific machine, requiring 12 minutes of assembly time per unit for product A and 25 minutes per unit for product B. The company's estimated effective machine working time per week is only 30 hours (due to maintenance or malfunctions). Technical constraints mean that for every five units of product A produced, at least two units of product B must be produced.

Try to formulate a model for this problem.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"profit_A": {"base":3,"perturb":{"mode":"rel","r":0.5}}
"profit_B": {"base":5,"perturb":{"mode":"rel","r":0.5}}
"assembly_time_A": {"base":12,"perturb":{"mode":"rel","r":0.5}}
"assembly_time_B": {"base":25,"perturb":{"mode":"rel","r":0.5}}
"weekly_machine_hours": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"ratio_A_per_5": {"base":5,"perturb":{"mode":"abs","lo":5.0,"hi":5.0,"integer":true}}
"ratio_B_min": {"base":2,"perturb":{"mode":"abs","lo":2.0,"hi":2.0,"integer":true}}
```

Warnings:

```
[ratio_A_per_5] degenerate abs range (lo == hi); perturbation has no effect
[ratio_B_min] degenerate abs range (lo == hi); perturbation has no effect
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.xA = pyo.Var(domain=pyo.NonNegativeReals)
    model.xB = pyo.Var(domain=pyo.NonNegativeReals)

    model.profit = pyo.Objective(
        expr=params["profit_A"] * model.xA + params["profit_B"] * model.xB,
        sense=pyo.maximize,
    )

    model.time_limit = pyo.Constraint(
        expr=params["assembly_time_A"] * model.xA
        + params["assembly_time_B"] * model.xB
        <= params["weekly_machine_hours"] * 60
    )

    # For every ratio_A_per_5 units of A, at least ratio_B_min units of B:
    # xB >= (ratio_B_min / ratio_A_per_5) * xA
    model.ratio = pyo.Constraint(
        expr=params["ratio_A_per_5"] * model.xB
        >= params["ratio_B_min"] * model.xA
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"products":["A","B"]},"params":["profit_A","profit_B","assembly_time_A","assembly_time_B","weekly_machine_hours","ratio_A_per_5","ratio_B_min"],"variables":{"quantity_A":{"type":"NonNegativeReals"},"quantity_B":{"type":"NonNegativeReals"}},"constraints":["assembly_time_A*quantity_A + assembly_time_B*quantity_B <= 60*weekly_machine_hours","ratio_A_per_5*quantity_B >= ratio_B_min*quantity_A"],"objective":{"sense":"maximize","expression":"profit_A*quantity_A + profit_B*quantity_B"},"constants":{"minutes_per_hour":60}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.profit_A = pyo.Param(initialize=params["profit_A"])
    model.profit_B = pyo.Param(initialize=params["profit_B"])
    model.assembly_time_A = pyo.Param(initialize=params["assembly_time_A"])
    model.assembly_time_B = pyo.Param(initialize=params["assembly_time_B"])
    model.weekly_machine_hours = pyo.Param(
        initialize=params["weekly_machine_hours"]
    )
    model.ratio_A_per_5 = pyo.Param(initialize=params["ratio_A_per_5"])
    model.ratio_B_min = pyo.Param(initialize=params["ratio_B_min"])

    # Continuous production quantities, as in a linear programming formulation.
    model.quantity_A = pyo.Var(domain=pyo.NonNegativeReals)
    model.quantity_B = pyo.Var(domain=pyo.NonNegativeReals)

    model.machine_capacity = pyo.Constraint(
        expr=(
            model.assembly_time_A * model.quantity_A
            + model.assembly_time_B * model.quantity_B
            <= 60 * model.weekly_machine_hours
        )
    )

    model.technical_ratio = pyo.Constraint(
        expr=(
            model.ratio_A_per_5 * model.quantity_B
            >= model.ratio_B_min * model.quantity_A
        )
    )

    model.total_profit = pyo.Objective(
        expr=(
            model.profit_A * model.quantity_A
            + model.profit_B * model.quantity_B
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    assembly_time_A = params["assembly_time_A"]  # minutes
    assembly_time_B = params["assembly_time_B"]  # minutes
    weekly_machine_hours = params["weekly_machine_hours"]  # hours
    ratio_A_per_5 = params["ratio_A_per_5"]  # units of A per ratio block
    ratio_B_min = params["ratio_B_min"]      # minimum units of B per ratio block

    weekly_machine_minutes = weekly_machine_hours * 60

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x_A = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_A")
    x_B = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_B")

    model.setObjective(profit_A * x_A + profit_B * x_B, GRB.MAXIMIZE)

    # Machine time constraint (convert hours to minutes)
    model.addConstr(
        assembly_time_A * x_A + assembly_time_B * x_B <= weekly_machine_minutes,
        name="machine_time"
    )

    # Technical ratio constraint: for every ratio_A_per_5 units of A, at least ratio_B_min units of B
    # i.e. x_B / x_A >= ratio_B_min / ratio_A_per_5
    # rewritten: ratio_A_per_5 * x_B >= ratio_B_min * x_A
    model.addConstr(
        ratio_A_per_5 * x_B >= ratio_B_min * x_A,
        name="technical_ratio"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 409.09090909090907 (optimal) | 409.09090909090907 (optimal) | 409.09090909090907 (optimal) |
| 1 | 601.5359183694418 (optimal) | 601.5359183694418 (optimal) | 601.5359183694418 (optimal) |
| 2 | 481.6273818438317 (optimal) | 481.6273818438317 (optimal) | 481.6273818438317 (optimal) |
| 3 | 668.2661861513941 (optimal) | 668.2661861513941 (optimal) | 668.266186151394 (optimal) |
| 4 | 354.0148127968438 (optimal) | 354.0148127968438 (optimal) | 354.0148127968438 (optimal) |
| 5 | 416.5923812213554 (optimal) | 416.5923812213554 (optimal) | 416.5923812213555 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 409.09090909090907 (optimal) | 409.09090909090907 (optimal) | 409.09090909090907 (optimal) |
| 1 | 601.5359183694418 (optimal) | 601.5359183694418 (optimal) | 601.5359183694418 (optimal) |
| 2 | 481.6273818438317 (optimal) | 481.6273818438317 (optimal) | 481.6273818438317 (optimal) |
| 3 | 668.2661861513941 (optimal) | 668.2661861513941 (optimal) | 668.266186151394 (optimal) |
| 4 | 354.0148127968438 (optimal) | 354.0148127968438 (optimal) | 354.0148127968438 (optimal) |
| 5 | 416.5923812213554 (optimal) | 416.5923812213554 (optimal) | 416.5923812213555 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 3. om_mamo_27 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_27` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 27) |
| Problem class (OptiMind) | ['Diet Problem'] |
| Optimization sense | not determined from the problem text (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 19.217560975609757 |
| Answer (OptiMind) | 22 |
| Rules that certify it | gate 19.217560975609757, gate_3fam 19.217560975609757, gate_tau 19.217560975609757, panel_base_2of3 19.217560975609757, panel_base_3of3 19.217560975609757, ind_gate 19.217560975609757, ind_gate_tau 19.217560975609757 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
Consider the following table of food and corresponding nutritional values: Bread contains 4 grams of protein, 7 grams of carbohydrates, has a calorie count of 130, and costs 3 dollar. Milk contains 6 grams of protein, 10 grams of carbohydrates, has a calorie count of 120, and costs 4 dollars. Fish is high in protein with 20 grams, contains no carbohydrates, has a calorie count of 150, and is the most expensive at 8 dollars. Potato contains 1 gram of protein, is high in carbohydrates with 30 grams, has the lowest calorie count at 70, and is the cheapest at 2 dollars. The ideal intake for an adult is at least 40 grams of protein, 50 grams of carbohydrates, and 450 calories per day. The problem is to find the least costly way to achieve those amounts of nutrition by using the four types of food shown in the table. 
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"protein_bread": {"base":4,"perturb":{"mode":"rel","r":0.3}}
"carb_bread": {"base":7,"perturb":{"mode":"rel","r":0.3}}
"cal_bread": {"base":130,"perturb":{"mode":"rel","r":0.25}}
"cost_bread": {"base":3,"perturb":{"mode":"abs","lo":1.5,"hi":6.0,"integer":false}}
"protein_milk": {"base":6,"perturb":{"mode":"rel","r":0.3}}
"carb_milk": {"base":10,"perturb":{"mode":"rel","r":0.3}}
"cal_milk": {"base":120,"perturb":{"mode":"rel","r":0.25}}
"cost_milk": {"base":4,"perturb":{"mode":"abs","lo":2.0,"hi":8.0,"integer":false}}
"protein_fish": {"base":20,"perturb":{"mode":"rel","r":0.3}}
"carb_fish": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":5.0,"integer":false}}
"cal_fish": {"base":150,"perturb":{"mode":"rel","r":0.25}}
"cost_fish": {"base":8,"perturb":{"mode":"abs","lo":4.0,"hi":16.0,"integer":false}}
"protein_potato": {"base":1,"perturb":{"mode":"rel","r":0.5}}
"carb_potato": {"base":30,"perturb":{"mode":"rel","r":0.3}}
"cal_potato": {"base":70,"perturb":{"mode":"rel","r":0.25}}
"cost_potato": {"base":2,"perturb":{"mode":"abs","lo":1.0,"hi":4.0,"integer":false}}
"req_protein": {"base":40,"perturb":{"mode":"rel","r":0.25}}
"req_carb": {"base":50,"perturb":{"mode":"rel","r":0.3}}
"req_cal": {"base":450,"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    foods = ["bread", "milk", "fish", "potato"]

    model = pyo.ConcreteModel()

    model.FOOD = pyo.Set(initialize=foods)

    protein = {f: params["protein_" + f] for f in foods}
    carb = {f: params["carb_" + f] for f in foods}
    cal = {f: params["cal_" + f] for f in foods}
    cost = {f: params["cost_" + f] for f in foods}

    model.x = pyo.Var(model.FOOD, domain=pyo.NonNegativeReals)

    model.protein_con = pyo.Constraint(
        expr=sum(protein[f] * model.x[f] for f in foods) >= params["req_protein"]
    )
    model.carb_con = pyo.Constraint(
        expr=sum(carb[f] * model.x[f] for f in foods) >= params["req_carb"]
    )
    model.cal_con = pyo.Constraint(
        expr=sum(cal[f] * model.x[f] for f in foods) >= params["req_cal"]
    )

    model.cost_obj = pyo.Objective(
        expr=sum(cost[f] * model.x[f] for f in foods), sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost_obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"foods":["bread","milk","fish","potato"]},"params":{"protein":{"bread":"protein_bread","milk":"protein_milk","fish":"protein_fish","potato":"protein_potato"},"carb":{"bread":"carb_bread","milk":"carb_milk","fish":"carb_fish","potato":"carb_potato"},"cal":{"bread":"cal_bread","milk":"cal_milk","fish":"cal_fish","potato":"cal_potato"},"cost":{"bread":"cost_bread","milk":"cost_milk","fish":"cost_fish","potato":"cost_potato"},"req_protein":"req_protein","req_carb":"req_carb","req_cal":"req_cal"},"variables":{"quantity[food]":"nonnegative continuous"},"constraints":["sum(protein[food]*quantity[food] for food in foods) >= req_protein","sum(carb[food]*quantity[food] for food in foods) >= req_carb","sum(cal[food]*quantity[food] for food in foods) >= req_cal"],"objective":"minimize sum(cost[food]*quantity[food] for food in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.foods = pyo.Set(
        initialize=["bread", "milk", "fish", "potato"],
        ordered=True,
    )

    model.protein = pyo.Param(
        model.foods,
        initialize={
            "bread": params["protein_bread"],
            "milk": params["protein_milk"],
            "fish": params["protein_fish"],
            "potato": params["protein_potato"],
        },
    )
    model.carb = pyo.Param(
        model.foods,
        initialize={
            "bread": params["carb_bread"],
            "milk": params["carb_milk"],
            "fish": params["carb_fish"],
            "potato": params["carb_potato"],
        },
    )
    model.cal = pyo.Param(
        model.foods,
        initialize={
            "bread": params["cal_bread"],
            "milk": params["cal_milk"],
            "fish": params["cal_fish"],
            "potato": params["cal_potato"],
        },
    )
    model.cost = pyo.Param(
        model.foods,
        initialize={
            "bread": params["cost_bread"],
            "milk": params["cost_milk"],
            "fish": params["cost_fish"],
            "potato": params["cost_potato"],
        },
    )

    model.req_protein = pyo.Param(initialize=params["req_protein"])
    model.req_carb = pyo.Param(initialize=params["req_carb"])
    model.req_cal = pyo.Param(initialize=params["req_cal"])

    model.quantity = pyo.Var(model.foods, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_protein
    )
    model.carb_requirement = pyo.Constraint(
        expr=sum(
            model.carb[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_carb
    )
    model.calorie_requirement = pyo.Constraint(
        expr=sum(
            model.cal[food] * model.quantity[food]
            for food in model.foods
        ) >= model.req_cal
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.quantity[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    protein_bread = params["protein_bread"]
    carb_bread = params["carb_bread"]
    cal_bread = params["cal_bread"]
    cost_bread = params["cost_bread"]

    protein_milk = params["protein_milk"]
    carb_milk = params["carb_milk"]
    cal_milk = params["cal_milk"]
    cost_milk = params["cost_milk"]

    protein_fish = params["protein_fish"]
    carb_fish = params["carb_fish"]
    cal_fish = params["cal_fish"]
    cost_fish = params["cost_fish"]

    protein_potato = params["protein_potato"]
    carb_potato = params["carb_potato"]
    cal_potato = params["cal_potato"]
    cost_potato = params["cost_potato"]

    req_protein = params["req_protein"]
    req_carb = params["req_carb"]
    req_cal = params["req_cal"]

    model = gp.Model("diet")
    model.setParam("OutputFlag", 0)

    bread = model.addVar(lb=0.0, name="bread")
    milk = model.addVar(lb=0.0, name="milk")
    fish = model.addVar(lb=0.0, name="fish")
    potato = model.addVar(lb=0.0, name="potato")

    model.setObjective(
        cost_bread * bread + cost_milk * milk + cost_fish * fish + cost_potato * potato,
        GRB.MINIMIZE
    )

    model.addConstr(
        protein_bread * bread + protein_milk * milk + protein_fish * fish + protein_potato * potato >= req_protein,
        name="protein_req"
    )
    model.addConstr(
        carb_bread * bread + carb_milk * milk + carb_fish * fish + carb_potato * potato >= req_carb,
        name="carb_req"
    )
    model.addConstr(
        cal_bread * bread + cal_milk * milk + cal_fish * fish + cal_potato * potato >= req_cal,
        name="cal_req"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 19.217560975609757 (optimal) | 19.217560975609757 (optimal) | 19.217560975609754 (optimal) |
| 1 | 12.664230548195949 (optimal) | 12.664230548195949 (optimal) | 12.664230548195949 (optimal) |
| 2 | 22.043245669382678 (optimal) | 22.043245669382678 (optimal) | 22.043245669382678 (optimal) |
| 3 | 15.057215161344331 (optimal) | 15.057215161344331 (optimal) | 15.057215161344331 (optimal) |
| 4 | 22.340874835616596 (optimal) | 22.340874835616596 (optimal) | 22.3408748356166 (optimal) |
| 5 | 23.952055965013198 (optimal) | 23.952055965013198 (optimal) | 23.952055965013198 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 19.217560975609757 (optimal) | 19.217560975609757 (optimal) | 19.217560975609754 (optimal) |
| 1 | 12.664230548195949 (optimal) | 12.664230548195949 (optimal) | 12.664230548195949 (optimal) |
| 2 | 22.043245669382678 (optimal) | 22.043245669382678 (optimal) | 22.043245669382678 (optimal) |
| 3 | 15.057215161344331 (optimal) | 15.057215161344331 (optimal) | 15.057215161344331 (optimal) |
| 4 | 22.340874835616596 (optimal) | 22.340874835616596 (optimal) | 22.3408748356166 (optimal) |
| 5 | 23.952055965013198 (optimal) | 23.952055965013198 (optimal) | 23.952055965013198 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 4. om_mamo_34 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_34` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 34) |
| Problem class (OptiMind) | ["TravelingSalesman"] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 198.0 |
| Answer (OptiMind) | 192 |
| Rules that certify it | gate 198.0, gate_3fam 198.0, gate_tau 198.0, panel_base_2of3 198.0, panel_base_3of3 198.0, ind_gate 198.0, ind_gate_tau 198.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
Consider a delivery company that operates in six cities, labelled from 1 to 6. The company needs to deliver packages to all cities, starting from any one of them, but following these constraints: each city should be visited exactly once, and after visiting all the cities, the delivery van should return to the city where it started. We need to minimize the total cost of this delivery route, taking into account factors such as fuel, road taxes, and driver fees.
Here are the associated costs between the cities:
The cost to deliver from City 1 to City 2 is 43 units, to City 3 is 39 units, to City 4 is 97 units, to City 5 is 84 units, and to City 6 is 67 units.
From City 2, the costs are 43 units to City 1, 18 units to City 3, 92 units to City 4, 27 units to City 5, and 51 units to City 6.
For deliveries from City 3, it costs 39 units to reach City 1, 18 units to reach City 2, 84 units to reach City 4, 60 units to reach City 5, and 15 units to reach City 6.
From City 4, the costs are 97 units to City 1, 92 units to City 2, 84 units to City 3, 42 units to City 5, and 32 units to City 6.
Delivering from City 5, the costs are 84 units to City 1, 27 units to City 2, 60 units to City 3, 42 units to City 4, and 18 units to City 6.
Lastly, from City 6, it costs 67 units to reach City 1, 51 units to reach City 2, 15 units to reach City 3, 32 units to reach City 4, and 18 units to reach City 5.
What is the minimum total delivery cost for the company to deliver to each city exactly once and return to the starting city?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_1_2": {"base":43,"perturb":{"mode":"rel","r":0.5}}
"cost_1_3": {"base":39,"perturb":{"mode":"rel","r":0.5}}
"cost_1_4": {"base":97,"perturb":{"mode":"rel","r":0.5}}
"cost_1_5": {"base":84,"perturb":{"mode":"rel","r":0.5}}
"cost_1_6": {"base":67,"perturb":{"mode":"rel","r":0.5}}
"cost_2_1": {"base":43,"perturb":{"mode":"rel","r":0.5}}
"cost_2_3": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"cost_2_4": {"base":92,"perturb":{"mode":"rel","r":0.5}}
"cost_2_5": {"base":27,"perturb":{"mode":"rel","r":0.5}}
"cost_2_6": {"base":51,"perturb":{"mode":"rel","r":0.5}}
"cost_3_1": {"base":39,"perturb":{"mode":"rel","r":0.5}}
"cost_3_2": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"cost_3_4": {"base":84,"perturb":{"mode":"rel","r":0.5}}
"cost_3_5": {"base":60,"perturb":{"mode":"rel","r":0.5}}
"cost_3_6": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"cost_4_1": {"base":97,"perturb":{"mode":"rel","r":0.5}}
"cost_4_2": {"base":92,"perturb":{"mode":"rel","r":0.5}}
"cost_4_3": {"base":84,"perturb":{"mode":"rel","r":0.5}}
"cost_4_5": {"base":42,"perturb":{"mode":"rel","r":0.5}}
"cost_4_6": {"base":32,"perturb":{"mode":"rel","r":0.5}}
"cost_5_1": {"base":84,"perturb":{"mode":"rel","r":0.5}}
"cost_5_2": {"base":27,"perturb":{"mode":"rel","r":0.5}}
"cost_5_3": {"base":60,"perturb":{"mode":"rel","r":0.5}}
"cost_5_4": {"base":42,"perturb":{"mode":"rel","r":0.5}}
"cost_5_6": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"cost_6_1": {"base":67,"perturb":{"mode":"rel","r":0.5}}
"cost_6_2": {"base":51,"perturb":{"mode":"rel","r":0.5}}
"cost_6_3": {"base":15,"perturb":{"mode":"rel","r":0.5}}
"cost_6_4": {"base":32,"perturb":{"mode":"rel","r":0.5}}
"cost_6_5": {"base":18,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5, 6]

    arcs = [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 1), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
            (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
            (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
            (6, 1), (6, 2), (6, 3), (6, 4), (6, 5)]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    # Each city has exactly one outgoing arc
    model.out_balance = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_balance = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (DFJ lazy-style constraints enumerated over all proper
    # non-trivial subsets): internal arcs in any subset S of size 2..n-1 <= |S|-1
    from itertools import combinations
    subsets = []
    for k in range(2, len(cities)):
        for sub in combinations(cities, k):
            subsets.append(sub)
    model.subsets = pyo.Set(initialize=list(range(len(subsets))), ordered=True)
    model.subset_order = pyo.Constraint(
        model.subsets,
        rule=lambda m, s: sum(
            m.x[(i, j)]
            for i in subsets[s]
            for j in subsets[s]
            if i != j
        ) <= len(subsets[s]) - 1,
    )

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","S":"{T subset V: 2 <= |T| <= 5}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A"},"constraints":["sum(x[i,j] for j in V if j != i) == 1 for each i in V","sum(x[i,j] for i in V if i != j) == 1 for each j in V","sum(x[i,j] for i in T for j in T if i != j) <= |T|-1 for each T in S"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    cities = tuple(range(1, 7))
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )
    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(current_model, i):
        return sum(
            current_model.route_arc[i, j]
            for j in cities
            if j != i
        ) == 1

    def incoming_rule(current_model, j):
        return sum(
            current_model.route_arc[i, j]
            for i in cities
            if i != j
        ) == 1

    model.outgoing_once = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_once = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
                sum(
                    model.route_arc[i, j]
                    for i in subset
                    for j in subset
                    if i != j
                ) <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.route_arc[i, j]
            for i, j in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    # Build cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # Subtour elimination variables (MTZ formulation)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints
    # Fix u[1] = 1 (city 1 is the starting reference)
    model.addConstr(u[1] == 1, name="u_start")

    for i in cities:
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n, name=f"u_ub_{i}")

    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 198.0 (optimal) | 198.0 (optimal) | 198.0 (optimal) |
| 1 | 154.60296743682656 (optimal) | 154.60296743682656 (optimal) | 154.6029674368266 (optimal) |
| 2 | 189.97848276997877 (optimal) | 189.97848276997877 (optimal) | 189.97848276997877 (optimal) |
| 3 | 188.28765842282021 (optimal) | 188.28765842282021 (optimal) | 188.28765842282021 (optimal) |
| 4 | 177.99151974234616 (optimal) | 177.99151974234616 (optimal) | 177.99151974234616 (optimal) |
| 5 | 178.32852637794824 (optimal) | 178.32852637794824 (optimal) | 178.32852637794824 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 198.0 (optimal) | 198.0 (optimal) | 198.0 (optimal) |
| 1 | 154.60296743682656 (optimal) | 154.60296743682656 (optimal) | 154.6029674368266 (optimal) |
| 2 | 189.97848276997877 (optimal) | 189.97848276997877 (optimal) | 189.97848276997877 (optimal) |
| 3 | 188.28765842282021 (optimal) | 188.28765842282021 (optimal) | 188.28765842282021 (optimal) |
| 4 | 177.99151974234616 (optimal) | 177.99151974234616 (optimal) | 177.99151974234616 (optimal) |
| 5 | 178.32852637794824 (optimal) | 178.32852637794824 (optimal) | 178.32852637794824 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 5. om_mamo_77 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_77` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 77) |
| Problem class (OptiMind) | ['Capacitated Facility Location Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 749131.9999999995 |
| Answer (OptiMind) | 749272 |
| Rules that certify it | gate 749131.9999999995, gate_3fam 749131.9999999995, gate_tau 749131.9999999995, panel_base_2of3 749131.9999999995, panel_base_3of3 749131.9999999995, ind_gate 749131.9999999995, ind_gate_tau 749131.9999999995 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any True (mismatch False, not_stated True) |
| Verification, family B (GPT-6.1 Sol) | flag_any True (mismatch False, not_stated True) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch False, not_stated True) |

### 2. Problem text

```
Welcome to the strategic challenge faced by DistribuMax, a company at a crossroads in optimizing its distribution network to efficiently supply nine unique retail stores. Each store has a specific demand that must be met to ensure customer satisfaction and operational success. DistribuMax can select from nine potential distribution centers, each with its own set of opening costs and capabilities. Furthermore, the cost of transporting goods from these centers to the retail stores varies, adding a layer of complexity to the decision-making process. The goal is to meet the demands of each retail store at the lowest possible total cost, which includes both the opening costs of the distribution centers and the transportation costs of the goods.

Given Data:
- Number of Potential Distribution Centers: 9
- Number of Retail Stores Needing Supply: 9

Opening Costs for Each Distribution Center (in dollars):
- Center 1: $151,000
- Center 2: $192,000
- Center 3: $114,000
- Center 4: $171,000
- Center 5: $160,000
- Center 6: $120,000
- Center 7: $182,000
- Center 8: $186,000
- Center 9: $174,000

Transportation Cost Per Unit from Each Distribution Center to Retail Stores (in dollars):
Costs vary from $1 to $5 per unit, with each distribution center offering a different rate to each store, reflecting the logistical complexity and geographical challenges of the distribution network:
- From Center 1: $2 to Store 1, $3 to Store 2, $4 to Store 3, $1 to Store 4, $5 to Store 5, $2 to Store 6, $3 to Store 7, $4 to Store 8, and $1 to Store 9.
- From Center 2: $5 to Store 1, $2 to Store 2, $3 to Store 3, $4 to Store 4, $1 to Store 5, $3 to Store 6, $5 to Store 7, $2 to Store 8, and $4 to Store 9.
- From Center 3: $3 to Store 1, $4 to Store 2, $2 to Store 3, $5 to Store 4, $3 to Store 5, $1 to Store 6, $2 to Store 7, $3 to Store 8, and $5 to Store 9.
- From Center 4: $1 to Store 1, $5 to Store 2, $4 to Store 3, $2 to Store 4, $4 to Store 5, $5 to Store 6, $3 to Store 7, $1 to Store 8, and $2 to Store 9.
- From Center 5: $4 to Store 1, $1 to Store 2, $5 to Store 3, $3 to Store 4, $2 to Store 5, $4 to Store 6, $1 to Store 7, $5 to Store 8, and $3 to Store 9.
- From Center 6: $2 to Store 1, $3 to Store 2, $1 to Store 3, $4 to Store 4, $5 to Store 5, $2 to Store 6, $4 to Store 7, $3 to Store 8, and $1 to Store 9.
- From Center 7: $3 to Store 1, $2 to Store 2, $3 to Store 3, $1 to Store 4, $4 to Store 5, $3 to Store 6, $5 to Store 7, $2 to Store 8, and $4 to Store 9.
- From Center 8: $5 to Store 1, $4 to Store 2, $2 to Store 3, $3 to Store 4, $1 to Store 5, $4 to Store 6, $2 to Store 7, $4 to Store 8, and $3 to Store 9.
- From Center 9: $4 to Store 1, $3 to Store 2, $4 to Store 3, $2 to Store 4, $3 to Store 5, $1 to Store 6, $3 to Store 7, $5 to Store 8, and $2 to Store 9.

Demand of Each Retail Store (in units):
- Store 1: 871 units
- Store 2: 462 units
- Store 3: 538 units
- Store 4: 898 units
- Store 5: 992 units
- Store 6: 791 units
- Store 7: 818 units
- Store 8: 688 units
- Store 9: 778 units

Supply Capacity of Each Distribution Center (in units):
- Capacities range from 840 units to 1856 units, with each center having a unique capacity to provide for the stores.

DistribuMax seeks to identify the optimal combination of distribution centers to open and the distribution of supplies to stores that will minimize the total operational cost. This includes meticulously planning which distribution centers to activate and how to distribute their inventory to meet the demands of the retail stores in the most cost-efficient manner.

Question:
What is the optimal total cost for DistribuMax to open distribution centers and transport goods to meet the demands of all nine retail stores, considering both the opening costs of the centers and the transportation costs of supplying the stores?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"opening_cost": {"base":[151000,192000,114000,171000,160000,120000,182000,186000,174000],"perturb":{"mode":"rel","r":0.35}}
"transport_cost": {"base":[[2,3,4,1,5,2,3,4,1],[5,2,3,4,1,3,5,2,4],[3,4,2,5,3,1,2,3,5],[1,5,4,2,4,5,3,1,2],[4,1,5,3,2,4,1,5,3],[2,3,1,4,5,2,4,3,1],[3,2,3,1,4,3,5,2,4],[5,4,2,3,1,4,2,4,3],[4,3,4,2,3,1,3,5,2]],"perturb":{"mode":"abs","lo":1.0,"hi":10.0,"integer":true}}
"demand": {"base":[871,462,538,898,992,791,818,688,778],"perturb":{"mode":"rel","r":0.25}}
"capacity": {"base":[840,1000,1100,1250,1350,1450,1550,1700,1856],"perturb":{"mode":"rel","r":0.2}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_centers = len(opening_cost)
    n_stores = len(demand)

    centers = range(n_centers)
    stores = range(n_stores)

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=list(centers))
    model.S = pyo.Set(initialize=list(stores))

    model.y = pyo.Var(model.C, within=pyo.Binary)
    model.x = pyo.Var(model.C, model.S, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(opening_cost[i] * mdl.y[i] for i in mdl.C) + sum(
            transport_cost[i][j] * mdl.x[i, j] for i in mdl.C for j in mdl.S
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.C) >= demand[j]

    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.S) <= capacity[i] * mdl.y[i]

    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"centers 0..8","J":"stores 0..8"},"params":{"opening_cost[i]":"params['opening_cost'][i]","transport_cost[i,j]":"params['transport_cost'][i][j]","demand[j]":"params['demand'][j]","capacity[i]":"params['capacity'][i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i shipment[i,j] == demand[j]","For each i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i sum_j transport_cost[i,j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input sequences, including nine supplied capacities."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 8)
    model.stores = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: opening_cost[i],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: transport_cost[i][j],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.demand[j]
        )

    model.demand_met = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_cost = params["opening_cost"]      # list of 9 floats
    transport_cost = params["transport_cost"]  # 9x9 matrix, rows=centers, cols=stores
    demand = params["demand"]                  # list of 9 floats
    capacity = params["capacity"]              # list of 9 floats

    n_centers = len(opening_cost)
    n_stores = len(demand)

    model = gp.Model("distribumax")
    model.Params.OutputFlag = 0

    open_c = model.addVars(n_centers, vtype=GRB.BINARY, name="open")
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS, lb=0, name="ship")

    # Meet every store's demand
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_centers)) == demand[j],
            name=f"demand_{j}",
        )

    # Center capacity, only if open
    for i in range(n_centers):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacity[i] * open_c[i],
            name=f"capacity_{i}",
        )

    model.setObjective(
        gp.quicksum(opening_cost[i] * open_c[i] for i in range(n_centers))
        + gp.quicksum(
            transport_cost[i][j] * ship[i, j]
            for i in range(n_centers)
            for j in range(n_stores)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed (status {model.Status})"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 749131.9999999995 (optimal) | 749132.0 (optimal) | 749132.0 (optimal) |
| 1 | 683336.9764508709 (optimal) | 683336.9764508709 (optimal) | 683336.9764508709 (optimal) |
| 2 | 708738.0110453035 (optimal) | 708738.0110453035 (optimal) | 708738.0110453037 (optimal) |
| 3 | 631114.8509290164 (optimal) | 631114.8509290147 (optimal) | 631114.8509290162 (optimal) |
| 4 | 736760.2276087081 (optimal) | 736760.2276087081 (optimal) | 736760.2276087082 (optimal) |
| 5 | 752556.1606760143 (optimal) | 752556.1606760144 (optimal) | 752556.1606760145 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 749131.9999999995 (optimal) | 749132.0 (optimal) | 749132.0 (optimal) |
| 1 | 683336.9764508709 (optimal) | 683336.9764508709 (optimal) | 683336.9764508709 (optimal) |
| 2 | 708738.0110453035 (optimal) | 708738.0110453035 (optimal) | 708738.0110453037 (optimal) |
| 3 | 631114.8509290164 (optimal) | 631114.8509290147 (optimal) | 631114.8509290162 (optimal) |
| 4 | 736760.2276087081 (optimal) | 736760.2276087081 (optimal) | 736760.2276087082 (optimal) |
| 5 | 752556.1606760143 (optimal) | 752556.1606760144 (optimal) | 752556.1606760145 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "capacity",
      "evidence": "Capacities range from 840 units to 1856 units, with each center having a unique capacity"
    }
  ]
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

```json
{"mismatch":[],"not_stated":[{"parameter":"capacity","evidence":"Capacities range from 840 units to 1856 units, with each center having a unique capacity to provide for the stores."}]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated True; flag_any True.

````json
```json
{
  "mismatch": [],
  "not_stated": [
    {
      "parameter": "capacity",
      "evidence": "Capacities range from 840 units to 1856 units, with each center having a unique capacity to provide for the stores."
    }
  ]
}
```
````


## 6. om_mamo_103 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_103` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 103) |
| Problem class (OptiMind) | ['Capacitated Facility Location Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 589621.0 |
| Answer (OptiMind) | 567010 |
| Rules that certify it | gate 589621.0, gate_3fam 589621.0, gate_tau 589621.0, panel_base_2of3 589621.0, panel_base_3of3 589621.0, ind_gate 589621.0, ind_gate_tau 589621.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
In the bustling marketplace of today, the fictional company GlobalSupply Inc. stands at a crucial juncture. It seeks to efficiently bridge its supply chain, connecting six potential distribution centers with nine eager retail stores scattered across the region. The objective is clear yet challenging: to minimize the total cost involved in opening distribution centers and transporting goods to fulfill the demands of the retail stores. This total cost encapsulates both the opening expenses of the distribution centers and the variable transportation costs per unit of goods delivered to the stores.

Here are the specifics:

- There are six Distribution Centers (DCs) under consideration for opening.
- Nine Retail Stores are in need of regular supplies.

The Opening Costs for each Distribution Center (in dollars) are as follows:
- DC 1: $151,000
- DC 2: $192,000
- DC 3: $114,000
- DC 4: $171,000
- DC 5: $160,000
- DC 6: $120,000

Transportation Cost Per Unit from each Distribution Center to each Retail Store (in dollars):
- From DC 1 to Stores: $2 to Store 1, $3 to Store 2, $4 to Store 3, $5 to Store 4, $6 to Store 5, $2 to Store 6, $3 to Store 7, $4 to Store 8, and $2 to Store 9
- From DC 2 to Stores: $4 to Store 1, $2 to Store 2, $3 to Store 3, $5 to Store 4, $4 to Store 5, $3 to Store 6, $4 to Store 7, $2 to Store 8, and $4 to Store 9
- From DC 3 to Stores: $1 to Store 1, $1 to Store 2, $2 to Store 3, $3 to Store 4, $4 to Store 5, $2 to Store 6, $1 to Store 7, $2 to Store 8, and $4 to Store 9
- From DC 4 to Stores: $4 to Store 1, $1 to Store 2, $2 to Store 3, $4 to Store 4, $3 to Store 5, $4 to Store 6, $2 to Store 7, $1 to Store 8, and $4 to Store 9
- From DC 5 to Stores: $1 to Store 1, $4 to Store 2, $5 to Store 3, $2 to Store 4, $3 to Store 5, $1 to Store 6, $2 to Store 7, $4 to Store 8, and $4 to Store 9
- From DC 6 to Stores: $4 to Store 1, $4 to Store 2, $4 to Store 3, $4 to Store 4, $4 to Store 5, $4 to Store 6, $4 to Store 7, $4 to Store 8, and $4 to Store 9

The Demand of each Retail Store (in units) ranges from 401 units for Store 1, 522 units for Store 2, 634 units for Store 3, 478 units for Store 4, 558 units for Store 5, 712 units for Store 6, 955 units for Store 7, 812 units for Store 8 and 603 units for Store 9, with varying demands for the others in between.

The Supply Capacity of each Distribution Center (in units) is also diverse, with DC 1 capable of supplying 1795 units, DC2 capable of supplying 1540 units, DC3 capable of supplying 1435 units, DC4 capable of supplying 1325 units, and DC5 capable of supplying 1325 units and DC6 capable of supplying 1095 units.

GlobalSupply Inc. now faces the daunting task of determining the optimal combination of distribution centers to open and the distribution of supplies to the retail stores in a way that the total opening and transportation costs are minimized.

**Question:**
What is the optimal total cost for GlobalSupply Inc. to both open the necessary distribution centers and transport goods to meet the demands of all nine retail stores, considering the given capacities and costs?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"opening_cost": {"base":[151000,192000,114000,171000,160000,120000],"perturb":{"mode":"rel","r":0.5}}
"transport_cost": {"base":[[2,3,4,5,6,2,3,4,2],[4,2,3,5,4,3,4,2,4],[1,1,2,3,4,2,1,2,4],[4,1,2,4,3,4,2,1,4],[1,4,5,2,3,1,2,4,4],[4,4,4,4,4,4,4,4,4]],"perturb":{"mode":"rel","r":0.5}}
"demand": {"base":[401,522,634,478,558,712,955,812,603],"perturb":{"mode":"rel","r":0.3}}
"capacity": {"base":[1795,1540,1435,1325,1325,1095],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = len(opening_cost)
    num_store = len(demand)

    dc_idx = list(range(num_dc))
    store_idx = list(range(num_store))

    model = pyo.ConcreteModel()

    model.DC = pyo.Set(initialize=dc_idx)
    model.STORE = pyo.Set(initialize=store_idx)

    model.y = pyo.Var(model.DC, domain=pyo.Binary)
    model.x = pyo.Var(model.DC, model.STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in m.DC) + sum(
            transport_cost[i][j] * m.x[i, j] for i in m.DC for j in m.STORE
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.DC) == demand[j]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.STORE) <= capacity[i] * m.y[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"DC":"0..5","Store":"0..8"},"params":{"opening_cost":"params['opening_cost'][i]","transport_cost":"params['transport_cost'][i][j]","demand":"params['demand'][j]","capacity":"params['capacity'][i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i][j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based input vectors and a row-major cost matrix."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.dc_set = pyo.RangeSet(0, 5)
    model.store_set = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: opening_cost[i],
    )
    model.transport_cost = pyo.Param(
        model.dc_set,
        model.store_set,
        initialize=lambda mdl, i, j: transport_cost[i][j],
    )
    model.demand = pyo.Param(
        model.store_set,
        initialize=lambda mdl, j: demand[j],
    )
    model.capacity = pyo.Param(
        model.dc_set,
        initialize=lambda mdl, i: capacity[i],
    )

    model.opened = pyo.Var(model.dc_set, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.dc_set,
        model.store_set,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return sum(
            mdl.shipment[i, j] for i in mdl.dc_set
        ) == mdl.demand[j]

    model.demand_constraints = pyo.Constraint(
        model.store_set, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return sum(
            mdl.shipment[i, j] for j in mdl.store_set
        ) <= mdl.capacity[i] * mdl.opened[i]

    model.capacity_constraints = pyo.Constraint(
        model.dc_set, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.dc_set
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.dc_set
                for j in model.store_set
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dcs = 6
    num_stores = 9
    dcs = range(num_dcs)
    stores = range(num_stores)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if DC i is opened
    y = model.addVars(dcs, vtype=GRB.BINARY, name="open")
    # x[i,j] = units shipped from DC i to store j
    x = model.addVars(dcs, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in dcs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in dcs for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in dcs) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from DC i cannot exceed its capacity (only if open)
    for i in dcs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacity[i] * y[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 589621.0 (optimal) | 589621.0 (optimal) | 589621.0 (optimal) |
| 1 | 464449.56155308936 (optimal) | 464449.56155308936 (optimal) | 464449.5615530894 (optimal) |
| 2 | 504591.69805741694 (optimal) | 504591.69805741694 (optimal) | 504591.69805741694 (optimal) |
| 3 | 610441.8082714077 (optimal) | 610441.8082714077 (optimal) | 610441.8082714075 (optimal) |
| 4 | 511103.57858229085 (optimal) | 511103.57858229085 (optimal) | 511103.57858229085 (optimal) |
| 5 | 525279.9733265027 (optimal) | 525279.9733265027 (optimal) | 525279.9733265027 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 589621.0 (optimal) | 589621.0 (optimal) | 589621.0 (optimal) |
| 1 | 464449.56155308936 (optimal) | 464449.56155308936 (optimal) | 464449.5615530894 (optimal) |
| 2 | 504591.69805741694 (optimal) | 504591.69805741694 (optimal) | 504591.69805741694 (optimal) |
| 3 | 610441.8082714077 (optimal) | 610441.8082714077 (optimal) | 610441.8082714075 (optimal) |
| 4 | 511103.57858229085 (optimal) | 511103.57858229085 (optimal) | 511103.57858229085 (optimal) |
| 5 | 525279.9733265027 (optimal) | 525279.9733265027 (optimal) | 525279.9733265027 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 7. om_mamo_114 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_114` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 114) |
| Problem class (OptiMind) | ['Capacitated Facility Location Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 588594.9999999998 |
| Answer (OptiMind) | 58895 |
| Rules that certify it | gate 588594.9999999998, gate_3fam 588594.9999999998, gate_tau 588594.9999999998, panel_base_2of3 588594.9999999998, panel_base_3of3 588594.9999999998, ind_gate 588594.9999999998, ind_gate_tau 588594.9999999998 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
In the bustling world of retail, GlobalSupply Inc. is at a crossroads, needing to efficiently distribute its products to eight retail stores scattered across the region. To achieve this, GlobalSupply Inc. must select from six potential distribution centers, each with its unique set of opening costs and capacities. The challenge lies not only in selecting which distribution centers to open but also in determining how to distribute their products in a way that minimizes the total cost, including both the opening of distribution centers and the transportation of goods to the stores.

Given Data:

Number of Potential Distribution Centers: 6

Number of Retail Stores Needing Supply: 8

Opening Costs for Each Distribution Center (in dollars):

Center 1: $151,000
Center 2: $192,000
Center 3: $114,000
Center 4: $171,000
Center 5: $160,000
Center 6: $120,000

Transportation Cost Per Unit from Each Distribution Center to Retail Stores (in dollars):

From Center 1: $2 to Store 1, $3 to Store 2, $4 to Store 3, $2 to Store 4, $3 to Store 5, $4 to Store 6, $4 to Store 7, $5 to Store 8
From Center 2: $2 to Store 1, $4 to Store 2, $3 to Store 3, $2 to Store 4, $4 to Store 5, $3 to Store 6, $2 to Store 7, $2 to Store 8
From Center 3: $5 to Store 1, $4 to Store 2, $3 to Store 3, $5 to Store 4, $4 to Store 5, $3 to Store 6, $4 to Store 7, $4 to Store 8
From Center 4: $4 to Store 1, $3 to Store 2, $2 to Store 3, $4 to Store 4, $3 to Store 5, $2 to Store 6, $3 to Store 7, $3 to Store 8
From Center 5: $5 to Store 1, $1 to Store 2, $2 to Store 3, $3 to Store 4, $4 to Store 5, $2 to Store 6, $3 to Store 7, $2 to Store 8
From Center 6: $1 to Store 1, $2 to Store 2, $2 to Store 3, $3 to Store 4, $1 to Store 5, $3 to Store 6, $4 to Store 7, $4 to Store 8

Demand of Each Retail Store (in units):

Store 1: 908 units
Store 2: 434 units
Store 3: 605 units
Store 4: 480 units
Store 5: 961 units
Store 6: 787 units
Store 7: 401 units
Store 8: 789 units

Supply Capacity of Each Distribution Center (in units):

Center 1: 1365 units
Center 2: 1929 units
Center 3: 1502 units
Center 4: 1201 units
Center 5: 1529 units
Center 6: 961 units

The optimal solution must navigate the intricate balance between opening costs, transportation costs, supply capacities, and the demands of the retail stores.

Question:
What is the optimal total cost for GlobalSupply Inc. to open distribution centers and transport goods to meet all the retail stores' demands, considering the cost of opening the centers and the transportation costs of supplying the stores?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"opening_cost": {"base":[151000,192000,114000,171000,160000,120000],"perturb":{"mode":"rel","r":0.3}}
"transport_cost": {"base":[[2,3,4,2,3,4,4,5],[2,4,3,2,4,3,2,2],[5,4,3,5,4,3,4,4],[4,3,2,4,3,2,3,3],[5,1,2,3,4,2,3,2],[1,2,2,3,1,3,4,4]],"perturb":{"mode":"rel","r":0.3}}
"demand": {"base":[908,434,605,480,961,787,401,789],"perturb":{"mode":"rel","r":0.2}}
"capacity": {"base":[1365,1929,1502,1201,1529,961],"perturb":{"mode":"rel","r":0.2}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)

    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=centers)
    model.stores = pyo.Set(initialize=stores)
    model.links = pyo.Set(
        initialize=[(c, s) for c in centers for s in stores], dimen=2
    )

    model.y = pyo.Var(model.centers, domain=pyo.Binary)
    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    model.opening_cost_expr = pyo.Expression(
        expr=sum(opening_cost[c] * model.y[c] for c in model.centers)
    )
    model.transport_cost_expr = pyo.Expression(
        expr=sum(
            transport_cost[c][s] * model.x[c, s] for c, s in model.links
        )
    )
    model.total_cost = pyo.Objective(
        expr=model.opening_cost_expr + model.transport_cost_expr,
        sense=pyo.minimize,
    )

    model.demand_con = pyo.Constraint(
        model.stores,
        rule=lambda m, s: sum(m.x[c, s] for c in m.centers) == demand[s],
    )

    model.capacity_con = pyo.Constraint(
        model.centers,
        rule=lambda m, c: sum(m.x[c, s] for s in m.stores) <= capacity[c] * m.y[c],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"1..6","J":"1..8"},"params":{"opening_cost":"f[i], i in I","transport_cost":"c[i,j], (i,j) in I x J","demand":"d[j], j in J","capacity":"u[i], i in I"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["sum(shipment[i,j] for i in I) == d[j], for each j in J","sum(shipment[i,j] for j in J) <= u[i]*opened[i], for each i in I"],"objective":"minimize sum(f[i]*opened[i] for i in I) + sum(c[i,j]*shipment[i,j] for i in I for j in J)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position):
    """Accept ordered sequences or dictionaries keyed by one-based indices."""
    if isinstance(data, Mapping):
        return data[position]
    return data[position - 1]


def _matrix_entry(data, center, store):
    """Also accept a dictionary keyed by (center, store) tuples."""
    if isinstance(data, Mapping) and (center, store) in data:
        return data[(center, store)]
    return _entry(_entry(data, center), store)


def solve(params):
    """Build and solve the capacitated distribution-center location model."""
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 6)
    model.stores = pyo.RangeSet(1, 8)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _entry(opening_cost, center),
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, center, store: _matrix_entry(
            transport_cost, center, store
        ),
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, store: _entry(demand, store),
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, center: _entry(capacity, center),
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[center, store] for center in mdl.centers)
            == mdl.demand[store]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, center):
        return (
            sum(mdl.shipment[center, store] for store in mdl.stores)
            <= mdl.capacity[center] * mdl.opened[center]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[center] * model.opened[center]
            for center in model.centers
        )
        + sum(
            model.transport_cost[center, store]
            * model.shipment[center, store]
            for center in model.centers
            for store in model.stores
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
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # dict or list, indexed by center 1..6
    transport_cost = params["transport_cost"]  # 6x8 matrix, rows=centers, cols=stores
    demand = params["demand"]               # indexed by store 1..8
    capacity = params["capacity"]           # indexed by center 1..6

    num_centers = 6
    num_stores = 8
    centers = range(num_centers)
    stores = range(num_stores)

    # Normalize indexing: support both 0-based lists and 1-based dicts
    def get_opening_cost(i):
        if isinstance(opening_cost, dict):
            return opening_cost.get(i + 1, opening_cost.get(i))
        return opening_cost[i]

    def get_transport_cost(i, j):
        row = transport_cost[i] if not isinstance(transport_cost, dict) else transport_cost.get(i + 1, transport_cost.get(i))
        if isinstance(row, dict):
            return row.get(j + 1, row.get(j))
        return row[j]

    def get_demand(j):
        if isinstance(demand, dict):
            return demand.get(j + 1, demand.get(j))
        return demand[j]

    def get_capacity(i):
        if isinstance(capacity, dict):
            return capacity.get(i + 1, capacity.get(i))
        return capacity[i]

    model = gp.Model("GlobalSupply_FLP")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if center i is opened
    y = model.addVars(num_centers, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from center i to store j
    x = model.addVars(num_centers, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(get_opening_cost(i) * y[i] for i in centers) +
        gp.quicksum(get_transport_cost(i, j) * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == get_demand(j),
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity if opened
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= get_capacity(i) * y[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 588594.9999999998 (optimal) | 588594.9999999998 (optimal) | 588595.0 (optimal) |
| 1 | 522805.55971546023 (optimal) | 522805.55971546023 (optimal) | 522805.5597154602 (optimal) |
| 2 | 511802.66273222154 (optimal) | 511802.6627322216 (optimal) | 511802.6627322216 (optimal) |
| 3 | 478532.65810854523 (optimal) | 478532.65810854523 (optimal) | 478532.6581085453 (optimal) |
| 4 | 425520.98997021053 (optimal) | 425520.9899702105 (optimal) | 425520.98997021053 (optimal) |
| 5 | 520315.9829933362 (optimal) | 520315.9829933362 (optimal) | 520315.9829933363 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 588594.9999999998 (optimal) | 588594.9999999998 (optimal) | 588595.0 (optimal) |
| 1 | 522805.55971546023 (optimal) | 522805.55971546023 (optimal) | 522805.5597154602 (optimal) |
| 2 | 511802.66273222154 (optimal) | 511802.6627322216 (optimal) | 511802.6627322216 (optimal) |
| 3 | 478532.65810854523 (optimal) | 478532.65810854523 (optimal) | 478532.6581085453 (optimal) |
| 4 | 425520.98997021053 (optimal) | 425520.9899702105 (optimal) | 425520.98997021053 (optimal) |
| 5 | 520315.9829933362 (optimal) | 520315.9829933362 (optimal) | 520315.9829933363 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{
  "mismatch": [],
  "not_stated": []
}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 8. om_mamo_131 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_131` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 131) |
| Problem class (OptiMind) | ['Diet Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 148.61089494163426 |
| Answer (OptiMind) | 178 |
| Rules that certify it | gate 148.61089494163426, gate_3fam 148.61089494163426, gate_tau 148.61089494163426, panel_base_2of3 148.61089494163426, panel_base_3of3 148.61089494163426, ind_gate 148.61089494163426, ind_gate_tau 148.61089494163426 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
International Wool Company operates a large farm on which sheep are raised. The farm manager determined that for the sheep to grow in the desired fashion, they need at least minimum amounts of four nutrients (the nutrients are nontoxic so the sheep can consume more than the minimum without harm). The manager is considering three different grains to feed the sheep. The nutrients listed are A, B, C, and D. For Grain 1: Nutrient A is present in the amount of 20 units per pound. Nutrient B is present in the amount of 10 units per pound. Nutrient C is present in the amount of 50 units per pound. Nutrient D is present in the amount of 6 units per pound. The cost of Grain 1 is 41 cents per pound. For Grain 2: Nutrient A is present in the amount of 30 units per pound. Nutrient B is present in the amount of 10 units per pound. Nutrient C is present in the amount of 30 units per pound. Nutrient D is present in the amount of 2.5 units per pound. The cost of Grain 2 is 36 cents per pound. For Grain 3: Nutrient A is present in the amount of 70 units per pound. Nutrient B is present in the amount of 0 units per pound. Nutrient C is present in the amount of 0 units per pound. Nutrient D is present in the amount of 10 units per pound. The cost of Grain 3 is 96 cents per pound. The minimum daily requirement for each nutrient is also listed: Nutrient A requires 110 units daily. Nutrient B requires 18 units daily. Nutrient C requires 90 units daily. Nutrient D requires 14 units daily. The manager believes that as long as a sheep receives the minimum daily amount of each nutrient, it will be healthy and produce a standard amount of wool. The manager wants to raise the sheep at minimum cost. Find the minimum cost in cents.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost_grain1": {"base":41,"perturb":{"mode":"rel","r":0.5}}
"cost_grain2": {"base":36,"perturb":{"mode":"rel","r":0.5}}
"cost_grain3": {"base":96,"perturb":{"mode":"rel","r":0.5}}
"nutrient_A_grain1": {"base":20,"perturb":{"mode":"rel","r":0.5}}
"nutrient_A_grain2": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"nutrient_A_grain3": {"base":70,"perturb":{"mode":"rel","r":0.5}}
"nutrient_B_grain1": {"base":10,"perturb":{"mode":"rel","r":0.7}}
"nutrient_B_grain2": {"base":10,"perturb":{"mode":"rel","r":0.7}}
"nutrient_B_grain3": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":5.0,"integer":false}}
"nutrient_C_grain1": {"base":50,"perturb":{"mode":"rel","r":0.5}}
"nutrient_C_grain2": {"base":30,"perturb":{"mode":"rel","r":0.5}}
"nutrient_C_grain3": {"base":0,"perturb":{"mode":"abs","lo":0.0,"hi":15.0,"integer":false}}
"nutrient_D_grain1": {"base":6,"perturb":{"mode":"rel","r":0.5}}
"nutrient_D_grain2": {"base":2.5,"perturb":{"mode":"rel","r":0.6}}
"nutrient_D_grain3": {"base":10,"perturb":{"mode":"rel","r":0.5}}
"req_A": {"base":110,"perturb":{"mode":"rel","r":0.5}}
"req_B": {"base":18,"perturb":{"mode":"rel","r":0.5}}
"req_C": {"base":90,"perturb":{"mode":"rel","r":0.5}}
"req_D": {"base":14,"perturb":{"mode":"rel","r":0.5}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    grains = ['1', '2', '3']
    nutrients = ['A', 'B', 'C', 'D']

    cost = {
        '1': params["cost_grain1"],
        '2': params["cost_grain2"],
        '3': params["cost_grain3"],
    }
    nutrient = {
        ('A', '1'): params["nutrient_A_grain1"],
        ('A', '2'): params["nutrient_A_grain2"],
        ('A', '3'): params["nutrient_A_grain3"],
        ('B', '1'): params["nutrient_B_grain1"],
        ('B', '2'): params["nutrient_B_grain2"],
        ('B', '3'): params["nutrient_B_grain3"],
        ('C', '1'): params["nutrient_C_grain1"],
        ('C', '2'): params["nutrient_C_grain2"],
        ('C', '3'): params["nutrient_C_grain3"],
        ('D', '1'): params["nutrient_D_grain1"],
        ('D', '2'): params["nutrient_D_grain2"],
        ('D', '3'): params["nutrient_D_grain3"],
    }
    req = {
        'A': params["req_A"],
        'B': params["req_B"],
        'C': params["req_C"],
        'D': params["req_D"],
    }

    model.x = pyo.Var(grains, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[g] * model.x[g] for g in grains),
        sense=pyo.minimize,
    )

    model.nutr_con = pyo.Constraint(
        nutrients,
        rule=lambda m, n: sum(nutrient[(n, g)] * m.x[g] for g in grains) >= req[n],
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {'objective': obj_val, 'status': 'optimal'}
    except Exception:
        return {'objective': None, 'status': 'infeasible or failed'}
```

#### B-structured.py

```python
# IR: {"sets":{"G":[1,2,3],"N":["A","B","C","D"]},"params":{"cost[g]":["cost_grain1","cost_grain2","cost_grain3"],"nutrient[A,g]":["nutrient_A_grain1","nutrient_A_grain2","nutrient_A_grain3"],"nutrient[B,g]":["nutrient_B_grain1","nutrient_B_grain2","nutrient_B_grain3"],"nutrient[C,g]":["nutrient_C_grain1","nutrient_C_grain2","nutrient_C_grain3"],"nutrient[D,g]":["nutrient_D_grain1","nutrient_D_grain2","nutrient_D_grain3"],"requirement[n]":["req_A","req_B","req_C","req_D"]},"variables":{"x[g]":{"type":"continuous","domain":"nonnegative","units":"pounds per sheep per day"}},"constraints":["For each n in N: sum(nutrient[n,g]*x[g] for g in G) >= requirement[n]"],"objective":{"sense":"minimize","expression":"sum(cost[g]*x[g] for g in G)","units":"cents per sheep per day"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    grains = (1, 2, 3)
    nutrients = ("A", "B", "C", "D")

    cost_data = {
        1: params["cost_grain1"],
        2: params["cost_grain2"],
        3: params["cost_grain3"],
    }
    nutrient_data = {
        ("A", 1): params["nutrient_A_grain1"],
        ("A", 2): params["nutrient_A_grain2"],
        ("A", 3): params["nutrient_A_grain3"],
        ("B", 1): params["nutrient_B_grain1"],
        ("B", 2): params["nutrient_B_grain2"],
        ("B", 3): params["nutrient_B_grain3"],
        ("C", 1): params["nutrient_C_grain1"],
        ("C", 2): params["nutrient_C_grain2"],
        ("C", 3): params["nutrient_C_grain3"],
        ("D", 1): params["nutrient_D_grain1"],
        ("D", 2): params["nutrient_D_grain2"],
        ("D", 3): params["nutrient_D_grain3"],
    }
    requirement_data = {
        "A": params["req_A"],
        "B": params["req_B"],
        "C": params["req_C"],
        "D": params["req_D"],
    }

    model = pyo.ConcreteModel()
    model.G = pyo.Set(initialize=grains, ordered=True)
    model.N = pyo.Set(initialize=nutrients, ordered=True)

    model.cost = pyo.Param(model.G, initialize=cost_data, within=pyo.Reals)
    model.nutrient = pyo.Param(
        model.N, model.G, initialize=nutrient_data, within=pyo.Reals
    )
    model.requirement = pyo.Param(
        model.N, initialize=requirement_data, within=pyo.Reals
    )

    model.x = pyo.Var(model.G, domain=pyo.NonNegativeReals)

    def nutrient_requirement_rule(instance, nutrient_id):
        return sum(
            instance.nutrient[nutrient_id, grain_id] * instance.x[grain_id]
            for grain_id in instance.G
        ) >= instance.requirement[nutrient_id]

    model.nutrient_requirements = pyo.Constraint(
        model.N, rule=nutrient_requirement_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[grain_id] * model.x[grain_id] for grain_id in model.G),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_grain1 = params["cost_grain1"]
    cost_grain2 = params["cost_grain2"]
    cost_grain3 = params["cost_grain3"]

    nutrient_A_grain1 = params["nutrient_A_grain1"]
    nutrient_A_grain2 = params["nutrient_A_grain2"]
    nutrient_A_grain3 = params["nutrient_A_grain3"]

    nutrient_B_grain1 = params["nutrient_B_grain1"]
    nutrient_B_grain2 = params["nutrient_B_grain2"]
    nutrient_B_grain3 = params["nutrient_B_grain3"]

    nutrient_C_grain1 = params["nutrient_C_grain1"]
    nutrient_C_grain2 = params["nutrient_C_grain2"]
    nutrient_C_grain3 = params["nutrient_C_grain3"]

    nutrient_D_grain1 = params["nutrient_D_grain1"]
    nutrient_D_grain2 = params["nutrient_D_grain2"]
    nutrient_D_grain3 = params["nutrient_D_grain3"]

    req_A = params["req_A"]
    req_B = params["req_B"]
    req_C = params["req_C"]
    req_D = params["req_D"]

    model = gp.Model("sheep_diet")
    model.setParam("OutputFlag", 0)

    # Decision variables: pounds of each grain to feed per day
    x1 = model.addVar(lb=0.0, name="x1")  # pounds of Grain 1
    x2 = model.addVar(lb=0.0, name="x2")  # pounds of Grain 2
    x3 = model.addVar(lb=0.0, name="x3")  # pounds of Grain 3

    # Objective: minimize total cost
    model.setObjective(
        cost_grain1 * x1 + cost_grain2 * x2 + cost_grain3 * x3,
        GRB.MINIMIZE
    )

    # Nutrient constraints (minimum daily requirements)
    model.addConstr(
        nutrient_A_grain1 * x1 + nutrient_A_grain2 * x2 + nutrient_A_grain3 * x3 >= req_A,
        name="nutrient_A"
    )
    model.addConstr(
        nutrient_B_grain1 * x1 + nutrient_B_grain2 * x2 + nutrient_B_grain3 * x3 >= req_B,
        name="nutrient_B"
    )
    model.addConstr(
        nutrient_C_grain1 * x1 + nutrient_C_grain2 * x2 + nutrient_C_grain3 * x3 >= req_C,
        name="nutrient_C"
    )
    model.addConstr(
        nutrient_D_grain1 * x1 + nutrient_D_grain2 * x2 + nutrient_D_grain3 * x3 >= req_D,
        name="nutrient_D"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 148.61089494163426 (optimal) | 148.61089494163426 (optimal) | 148.61089494163426 (optimal) |
| 1 | 154.53670685679896 (optimal) | 154.53670685679896 (optimal) | 154.53670685679896 (optimal) |
| 2 | 113.36947091005015 (optimal) | 113.36947091005015 (optimal) | 113.36947091005015 (optimal) |
| 3 | 280.68117470082797 (optimal) | 280.68117470082797 (optimal) | 280.68117470082797 (optimal) |
| 4 | 152.33303274664794 (optimal) | 152.33303274664794 (optimal) | 152.33303274664794 (optimal) |
| 5 | 147.24903700191683 (optimal) | 147.24903700191683 (optimal) | 147.2490370019168 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 148.61089494163426 (optimal) | 148.61089494163426 (optimal) | 148.61089494163426 (optimal) |
| 1 | 154.53670685679896 (optimal) | 154.53670685679896 (optimal) | 154.53670685679896 (optimal) |
| 2 | 113.36947091005015 (optimal) | 113.36947091005015 (optimal) | 113.36947091005015 (optimal) |
| 3 | 280.68117470082797 (optimal) | 280.68117470082797 (optimal) | 280.68117470082797 (optimal) |
| 4 | 152.33303274664794 (optimal) | 152.33303274664794 (optimal) | 152.33303274664794 (optimal) |
| 5 | 147.24903700191683 (optimal) | 147.24903700191683 (optimal) | 147.2490370019168 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 9. om_mamo_194 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_194` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 194) |
| Problem class (OptiMind) | ["Facility Location Problem (FLP)"] |
| Optimization sense | max (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 66.3661 |
| Answer (OptiMind) | 66.39 |
| Rules that certify it | gate 66.3661, gate_3fam 66.3661, gate_tau 66.3661, panel_base_2of3 66.3661, panel_base_3of3 66.3661, ind_gate 66.3661, ind_gate_tau 66.3661 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
The Chinese University of Hong Kong, Shenzhen decides to build a circular fountain on the campus. The school wants the fountain to be round and as large as possible but it must be restricted in a polygonal construction field, which is given by the following points: (0, 1), (0, 6), (4, 10), (8, 10), (11, 7), (11, 4), (7, 0), and (1, 0), the unit is m. Give a linear optimization formulation and find the maximal area. Keep your answer in four significant digit number.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"field_vertices": {"base":[[0,1],[0,6],[4,10],[8,10],[11,7],[11,4],[7,0],[1,0]],"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
[field_vertices] malformed abs bounds (lo/hi not scalar); fell back to rel +/-30% around base
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
import math
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    field_vertices = params["field_vertices"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(within=pyo.Reals)
    model.y = pyo.Var(within=pyo.Reals)
    model.r = pyo.Var(within=pyo.Reals, bounds=(0, None))

    n = len(field_vertices)
    model.constraints = pyo.ConstraintList()

    # Compute signed area to determine orientation
    area2 = 0.0
    for i in range(n):
        x1, y1 = field_vertices[i]
        x2, y2 = field_vertices[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1
    ccw = area2 > 0

    for i in range(n):
        x1, y1 = field_vertices[i]
        x2, y2 = field_vertices[(i + 1) % n]

        dx = x2 - x1
        dy = y2 - y1
        norm = math.sqrt(dx * dx + dy * dy)
        if ccw:
            nx = -dy / norm
            ny = dx / norm
        else:
            nx = dy / norm
            ny = -dx / norm

        model.constraints.add(
            nx * (model.x - x1) + ny * (model.y - y1) >= model.r
        )

    model.obj = pyo.Objective(expr=model.r, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    area = math.pi * obj_val * obj_val
    return {"objective": round(area, 4), "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"V":"vertex indices","E":"consecutive vertex pairs, cyclic"},"params":{"field_vertices":"ordered vertices of a convex polygon"},"derived":{"orientation":"sign of polygon signed area","edge_length[i]":"Euclidean length of edge i"},"variables":{"center_x":"Real","center_y":"Real","radius":"NonNegativeReal"},"constraints":["For each edge i=(u,v): orientation*((v.x-u.x)*(center_y-u.y)-(v.y-u.y)*(center_x-u.x)) >= edge_length[i]*radius"],"objective":"maximize radius (linear; equivalent to maximizing circular area)","report":"objective = pi*optimal_radius**2, rounded to four significant digits"}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = [
        (float(point[0]), float(point[1]))
        for point in params["field_vertices"]
    ]

    # Accept either an open vertex sequence or one repeating its first vertex.
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices = vertices[:-1]

    vertex_count = len(vertices)
    if vertex_count < 3:
        return {"objective": None, "status": "invalid_polygon"}

    if not all(
        math.isfinite(coordinate)
        for point in vertices
        for coordinate in point
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    signed_twice_area = sum(
        vertices[idx][0] * vertices[(idx + 1) % vertex_count][1]
        - vertices[(idx + 1) % vertex_count][0] * vertices[idx][1]
        for idx in range(vertex_count)
    )
    if signed_twice_area == 0:
        return {"objective": None, "status": "degenerate_polygon"}

    orientation = 1 if signed_twice_area > 0 else -1
    edge_data = []
    for idx in range(vertex_count):
        start_x, start_y = vertices[idx]
        end_x, end_y = vertices[(idx + 1) % vertex_count]
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        edge_length = math.hypot(delta_x, delta_y)
        if edge_length == 0:
            return {"objective": None, "status": "degenerate_edge"}
        edge_data.append(
            (start_x, start_y, delta_x, delta_y, edge_length)
        )

    model = pyo.ConcreteModel()
    model.edge_ids = pyo.RangeSet(0, vertex_count - 1)
    model.center_x = pyo.Var(domain=pyo.Reals)
    model.center_y = pyo.Var(domain=pyo.Reals)
    model.radius = pyo.Var(domain=pyo.NonNegativeReals)

    def containment_rule(problem, idx):
        start_x, start_y, delta_x, delta_y, edge_length = edge_data[idx]
        return (
            orientation
            * (
                delta_x * (problem.center_y - start_y)
                - delta_y * (problem.center_x - start_x)
            )
            >= edge_length * problem.radius
        )

    model.containment = pyo.Constraint(
        model.edge_ids, rule=containment_rule
    )
    model.radius_objective = pyo.Objective(
        expr=model.radius, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.radius_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # The LP maximizes radius; report the requested maximal area in m².
    obj_val = float(format(math.pi * obj_val**2, ".4g"))
    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    vertices = params["field_vertices"]
    n = len(vertices)

    # Build edge constraints for Chebyshev center LP
    # For each edge of the polygon, the distance from center (cx, cy) to the edge >= r
    # Edge from v[i] to v[i+1]: ax + by <= c, with (a,b) unit normal pointing inward
    # We need to determine the inward-pointing normal for each edge.

    # Compute polygon area sign to determine orientation (CCW or CW)
    area_sign = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        area_sign += (x1 * y2 - x2 * y1)
    # area_sign > 0 => CCW, < 0 => CW

    edges = []
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        # Edge vector
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        # Outward normal for CCW polygon: (dy, -dx) / length
        # Inward normal: (-dy, dx) / length
        if area_sign > 0:
            # CCW: inward normal is (-dy, dx) / length
            nx = -dy / length
            ny = dx / length
        else:
            # CW: inward normal is (dy, -dx) / length
            nx = dy / length
            ny = -dx / length
        # The constraint: nx*(cx - x1) + ny*(cy - y1) >= r
        # i.e., nx*cx + ny*cy - r >= nx*x1 + ny*y1
        rhs = nx * x1 + ny * y1
        edges.append((nx, ny, rhs))

    try:
        model = gp.Model()
        model.setParam("OutputFlag", 0)

        cx = model.addVar(lb=-GRB.INFINITY, name="cx")
        cy = model.addVar(lb=-GRB.INFINITY, name="cy")
        r = model.addVar(lb=0.0, name="r")

        for idx, (nx, ny, rhs) in enumerate(edges):
            model.addConstr(nx * cx + ny * cy - r >= rhs, name=f"edge_{idx}")

        model.setObjective(r, GRB.MAXIMIZE)
        model.optimize()

        if model.Status == GRB.OPTIMAL:
            radius = r.X
            area = math.pi * radius * radius
            return {"objective": float(area), "status": "optimal"}
        elif model.Status == GRB.INFEASIBLE:
            return {"objective": None, "status": "infeasible"}
        else:
            return {"objective": None, "status": f"gurobi_status_{model.Status}"}

    except gp.GurobiError as e:
        return {"objective": None, "status": f"gurobi_error: {str(e)}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 66.3661 (optimal) | 66.37 (optimal) | 66.36614480708437 (optimal) |
| 1 | 44.7583 (optimal) | 44.76 (optimal) | 44.75829754394167 (optimal) |
| 2 | 37.9164 (optimal) | 37.92 (optimal) | 37.916408977702766 (optimal) |
| 3 | 51.6454 (optimal) | 51.65 (optimal) | 51.64537647806785 (optimal) |
| 4 | 58.1161 (optimal) | 58.12 (optimal) | 58.11614267657511 (optimal) |
| 5 | 71.8607 (optimal) | 71.86 (optimal) | 71.86070227696729 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 66.3661 (optimal) | 66.37 (optimal) | 66.36614480708437 (optimal) |
| 1 | 44.7583 (optimal) | 44.76 (optimal) | 44.75829754394167 (optimal) |
| 2 | 37.9164 (optimal) | 37.92 (optimal) | 37.916408977702766 (optimal) |
| 3 | 51.6454 (optimal) | 51.65 (optimal) | 51.64537647806785 (optimal) |
| 4 | 58.1161 (optimal) | 58.12 (optimal) | 58.11614267657511 (optimal) |
| 5 | 71.8607 (optimal) | 71.86 (optimal) | 71.86070227696729 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````


## 10. om_mamo_197 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_197` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 197) |
| Problem class (OptiMind) | ['Diet Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 38.0 |
| Answer (OptiMind) | 24 |
| Rules that certify it | gate 38.0, gate_3fam 38.0, gate_tau 38.0, panel_base_2of3 38.0, panel_base_3of3 38.0, ind_gate 38.0, ind_gate_tau 38.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any True (mismatch True, not_stated False) |

### 2. Problem text

```
Imagine you are a dietitian, working diligently to provide a balanced diet plan for a client while keeping the cost to a minimum. The client's daily dietary requirement is 88 grams of protein, 144 grams of protein, and 1900 calories. To achieve this, you have a variety of six food items to choose from. Each food item comes with its specific nutritional values and price. 

Here's a detailed breakdown of each food item:

- Food 1: A high-protein food that offers 15 grams of protein, 10 grams of carbohydrates, and 163 calories, costing $10.
- Food 2: A balanced food offering 16 grams of protein, 25 grams of carbohydrates, and 108 calories, costing just $4.
- Food 3: A calorie-dense food providing 3 grams of protein, 8 grams of carbohydrates, and a whopping 198 calories, costing just $1.
- Food 4: A well-rounded food item that gives 19 grams of protein, 20 grams of carbohydrates, and 141 calories, priced at $7.
- Food 5: A modest food item that offers 11 grams of protein, 8 grams of carbohydrates, and 105 calories, costing $6.
- Food 6: Another calorie-dense food that delivers 10 grams of protein, 9 grams of carbohydrates, and 199 calories, costing $8.

Your task is to design a daily meal plan that meets all the client's requirements using the given food items while keeping the cost as low as possible. What is the minimum cost you can achieve while meeting the client's nutritional requirements? You could only assign integral portions of each type of food.
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"cost": {"base":[10,4,1,7,6,8],"perturb":{"mode":"rel","r":0.5}}
"protein": {"base":[15,16,3,19,11,10],"perturb":{"mode":"rel","r":0.3}}
"carbs": {"base":[10,25,8,20,8,9],"perturb":{"mode":"rel","r":0.3}}
"calories": {"base":[163,108,198,141,105,199],"perturb":{"mode":"rel","r":0.2}}
"protein_req_1": {"base":88,"perturb":{"mode":"rel","r":0.4}}
"protein_req_2": {"base":144,"perturb":{"mode":"rel","r":0.4}}
"calorie_req": {"base":1900,"perturb":{"mode":"rel","r":0.3}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req_1 = params["protein_req_1"]
    protein_req_2 = params["protein_req_2"]
    calorie_req = params["calorie_req"]

    n = len(cost)

    model = pyo.ConcreteModel()

    # Structural constants may be inline; only numeric params come from dict.
    model.FOODS = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.FOODS, domain=pyo.NonNegativeIntegers)

    def cost_rule(m):
        return sum(cost[i] * m.x[i] for i in m.FOODS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def protein1_rule(m):
        return sum(protein[i] * m.x[i] for i in m.FOODS) >= protein_req_1

    def protein2_rule(m):
        return sum(protein[i] * m.x[i] for i in m.FOODS) >= protein_req_2

    def calorie_rule(m):
        return sum(calories[i] * m.x[i] for i in m.FOODS) >= calorie_req

    model.protein_cons_1 = pyo.Constraint(rule=protein1_rule)
    model.protein_cons_2 = pyo.Constraint(rule=protein2_rule)
    model.calorie_cons = pyo.Constraint(rule=calorie_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible or solver failed"}
```

#### B-structured.py

```python
# IR: {"sets":{"foods":[0,1,2,3,4,5]},"params":{"cost":"food-indexed costs","protein":"food-indexed protein grams","carbs":"food-indexed carbohydrate grams; informational only","calories":"food-indexed calories","protein_req_1":"first minimum daily protein","protein_req_2":"second minimum daily protein","calorie_req":"minimum daily calories"},"variables":{"portions[foods]":"nonnegative integer"},"constraints":["sum(protein[i]*portions[i] for i in foods) >= protein_req_1","sum(protein[i]*portions[i] for i in foods) >= protein_req_2","sum(calories[i]*portions[i] for i in foods) >= calorie_req"],"objective":"minimize sum(cost[i]*portions[i] for i in foods)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Food data must be sequences or mappings indexed from 0 through 5.

    Both protein requirements are enforced as written. Carbohydrate data
    are retained, but no carbohydrate requirement is specified.
    """
    model = pyo.ConcreteModel()
    model.foods = pyo.RangeSet(0, 5)

    model.cost = pyo.Param(
        model.foods,
        initialize={food: params["cost"][food] for food in model.foods},
    )
    model.protein = pyo.Param(
        model.foods,
        initialize={food: params["protein"][food] for food in model.foods},
    )
    model.carbs = pyo.Param(
        model.foods,
        initialize={food: params["carbs"][food] for food in model.foods},
    )
    model.calories = pyo.Param(
        model.foods,
        initialize={food: params["calories"][food] for food in model.foods},
    )
    model.protein_req_1 = pyo.Param(initialize=params["protein_req_1"])
    model.protein_req_2 = pyo.Param(initialize=params["protein_req_2"])
    model.calorie_req = pyo.Param(initialize=params["calorie_req"])

    model.portions = pyo.Var(model.foods, domain=pyo.NonNegativeIntegers)

    model.protein_minimum_1 = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req_1
    )
    model.protein_minimum_2 = pyo.Constraint(
        expr=sum(
            model.protein[food] * model.portions[food]
            for food in model.foods
        ) >= model.protein_req_2
    )
    model.calorie_minimum = pyo.Constraint(
        expr=sum(
            model.calories[food] * model.portions[food]
            for food in model.foods
        ) >= model.calorie_req
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[food] * model.portions[food]
            for food in model.foods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    protein = params["protein"]
    carbs = params["carbs"]
    calories = params["calories"]
    protein_req_1 = params["protein_req_1"]
    protein_req_2 = params["protein_req_2"]
    calorie_req = params["calorie_req"]

    n_foods = len(cost)
    foods = range(n_foods)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(foods, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(gp.quicksum(cost[i] * x[i] for i in foods), GRB.MINIMIZE)

    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req_1, name="protein1")
    model.addConstr(gp.quicksum(protein[i] * x[i] for i in foods) >= protein_req_2, name="protein2")
    model.addConstr(gp.quicksum(calories[i] * x[i] for i in foods) >= calorie_req, name="calorie")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 38.0 (optimal) | 38.0 (optimal) | 38.0 (optimal) |
| 1 | 23.325518164014035 (optimal) | 23.325518164014035 (optimal) | 23.325518164014035 (optimal) |
| 2 | 38.217093481108144 (optimal) | 38.217093481108144 (optimal) | 38.217093481108144 (optimal) |
| 3 | 25.503268631527686 (optimal) | 25.503268631527686 (optimal) | 25.503268631527686 (optimal) |
| 4 | 40.108329099575556 (optimal) | 40.108329099575556 (optimal) | 40.108329099575556 (optimal) |
| 5 | 53.43723355257636 (optimal) | 53.43723355257636 (optimal) | 53.43723355257636 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 38.0 (optimal) | 38.0 (optimal) | 38.0 (optimal) |
| 1 | 23.325518164014035 (optimal) | 23.325518164014035 (optimal) | 23.325518164014035 (optimal) |
| 2 | 38.217093481108144 (optimal) | 38.217093481108144 (optimal) | 38.217093481108144 (optimal) |
| 3 | 25.503268631527686 (optimal) | 25.503268631527686 (optimal) | 25.503268631527686 (optimal) |
| 4 | 40.108329099575556 (optimal) | 40.108329099575556 (optimal) | 40.108329099575556 (optimal) |
| 5 | 53.43723355257636 (optimal) | 53.43723355257636 (optimal) | 53.43723355257636 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch True; flag_not_stated False; flag_any True.

````json
```json
{
  "mismatch": [
    {
      "parameter": "protein_req_2",
      "extracted": 144,
      "stated": "144 grams of carbohydrates (not protein)",
      "evidence": "The client's daily dietary requirement is 88 grams of protein, 144 grams of protein, and 1900 calories"
    }
  ],
  "not_stated": []
}
```
````


## 11. om_mamo_206 (OptiMind Mamo-Complex)

### 1. Identification

| Field | Value |
|---|---|
| Sample id | `om_mamo_206` |
| Benchmark | OptiMind Mamo-Complex (`datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv`, 0-based row 206) |
| Problem class (OptiMind) | ['Capacitated Facility Location Problem'] |
| Optimization sense | min (words "minim..." / "maxim..." in the problem text) |
| Certified value (panel_base_3of3) | 580131.0 |
| Answer (OptiMind) | 610975 |
| Rules that certify it | gate 580131.0, gate_3fam 580131.0, gate_tau 580131.0, panel_base_2of3 580131.0, panel_base_3of3 580131.0, ind_gate 580131.0, ind_gate_tau 580131.0 |
| Families agreeing at instance 0 | A (DeepSeek-V4-Flash) and B (GPT-6.1 Sol), A (DeepSeek-V4-Flash) and C (Claude Sonnet 5.5), B (GPT-6.1 Sol) and C (Claude Sonnet 5.5) |
| Verification, family A (DeepSeek-V4-Flash) | flag_any False (mismatch False, not_stated False) |
| Verification, family B (GPT-6.1 Sol) | flag_any False (mismatch False, not_stated False) |
| Verification, family C (Claude Sonnet 5.5) | flag_any False (mismatch False, not_stated False) |

### 2. Problem text

```
In the bustling world of retail, a company named SupplyChain Masters is faced with the challenge of efficiently supplying its nine retail stores with products from a network of seven potential distribution centers. The company's goal is to ensure that each store's demand is met, while simultaneously minimizing the total cost involved. This total cost encompasses the opening expenses of the distribution centers and the transportation costs for delivering the goods to the stores.

Let's dive into the specifics:

- The company is contemplating between seven distribution centers to serve its needs.
- There are nine retail stores scattered in different locations, each with its unique demand for products.

Opening Costs for Each Distribution Center (in dollars):
- Center 1: 151,000
- Center 2: 192,000
- Center 3: 114,000
- Center 4: 171,000
- Center 5: 160,000
- Center 6: 120,000
- Center 7: 182,000

Transportation Cost Per Unit from Each Distribution Center to Retail Stores (in dollars):
- From Center 1: $2 to Store 1, $3 to Store 2, $4 to Store 3, $5 to Store 4, $3 to Store 5, $2 to Store 6, $3 to Store 7, $4 to Store 8, and $2 to Store 9.
- From Center 2: $3 to Store 1, $2 to Store 2, $5 to Store 3, $4 to Store 4, $3 to Store 5, $2 to Store 6, $4 to Store 7, $3 to Store 8, and $4 to Store 9.
- From Center 3: $4 to Store 1, $3 to Store 2, $2 to Store 3, $3 to Store 4, $5 to Store 5, $4 to Store 6, $5 to Store 7, $3 to Store 8, and $5 to Store 9.
- From Center 4: $5 to Store 1, $4 to Store 2, $3 to Store 3, $2 to Store 4, $4 to Store 5, $5 to Store 6, $2 to Store 7, $4 to Store 8, and $3 to Store 9.
- From Center 5: $2 to Store 1, $5 to Store 2, $4 to Store 3, $3 to Store 4, $2 to Store 5, $3 to Store 6, $4 to Store 7, $5 to Store 8, and $3 to Store 9.
- From Center 6: $3 to Store 1, $4 to Store 2, $5 to Store 3, $3 to Store 4, $4 to Store 5, $2 to Store 6, $3 to Store 7, $4 to Store 8, and $2 to Store 9.
- From Center 7: $1 to Store 1, $2 to Store 2, $3 to Store 3, $4 to Store 4, $5 to Store 5, $3 to Store 6, $2 to Store 7, $1 to Store 8, and $2 to Store 9.

Demand of Each Retail Store (in units):
- Store 1: 440
- Store 2: 712
- Store 3: 860
- Store 4: 504
- Store 5: 892
- Store 6: 738
- Store 7: 651
- Store 8: 580
- Store 9: 790

Supply Capacity of Each Distribution Center (in units):
- Center 1: 1800
- Center 2: 1300
- Center 3: 1600
- Center 4: 1200
- Center 5: 1700
- Center 6: 814
- Center 7: 1962

SupplyChain Masters' challenge is to calculate the optimal setup of distribution centers that should be opened and determine the distribution of supplies to the retail stores in a way that all stores' demands are met at the lowest possible total cost.

Question:
What is the optimal total cost for SupplyChain Masters to open the necessary distribution centers and transport goods to all retail stores, considering both the opening costs and the transportation costs?
```

### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)

```json
"opening_cost": {"base":[151000,192000,114000,171000,160000,120000,182000],"perturb":{"mode":"rel","r":0.3}}
"transport_cost": {"base":[[2,3,4,5,3,2,3,4,2],[3,2,5,4,3,2,4,3,4],[4,3,2,3,5,4,5,3,5],[5,4,3,2,4,5,2,4,3],[2,5,4,3,2,3,4,5,3],[3,4,5,3,4,2,3,4,2],[1,2,3,4,5,3,2,1,2]],"perturb":{"mode":"rel","r":0.4}}
"demand": {"base":[440,712,860,504,892,738,651,580,790],"perturb":{"mode":"rel","r":0.25}}
"capacity": {"base":[1800,1300,1600,1200,1700,814,1962],"perturb":{"mode":"rel","r":0.25}}
```

Warnings:

```
none
```

Extraction attempts: 1.

### 4. Programs

#### A-direct.py

```python
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = len(opening_cost)
    num_stores = len(demand)
    centers = list(range(num_centers))
    stores = list(range(num_stores))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def trans_rule(mdl, i, j):
        return mdl.x[i, j]

    def open_rule(mdl, i):
        return mdl.y[i]

    model.trans_cost = pyo.Expression(centers, stores, rule=trans_rule)
    model.open_cost = pyo.Expression(centers, rule=open_rule)

    def obj_rule(mdl):
        return (
            sum(opening_cost[i] * mdl.y[i] for i in centers)
            + sum(transport_cost[i][j] * mdl.x[i, j] for i in centers for j in stores)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in centers) == demand[j]

    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def cap_rule(mdl, i):
        return sum(mdl.x[i, j] for j in stores) <= capacity[i] * mdl.y[i]

    model.cap_con = pyo.Constraint(centers, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}
```

#### B-structured.py

```python
# IR: {"sets":{"I":"1..7","J":"1..9"},"params":{"opening_cost":"I; params['opening_cost'][i-1]","transport_cost":"I x J; params['transport_cost'][i-1][j-1]","demand":"J; params['demand'][j-1]","capacity":"I; params['capacity'][i-1]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i shipment[i,j] = demand[j]","For each i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the facility-location problem using zero-based input arrays."""
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 7)
    model.stores = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            i: params["opening_cost"][i - 1]
            for i in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): params["transport_cost"][i - 1][j - 1]
            for i in model.centers
            for j in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            j: params["demand"][j - 1]
            for j in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            i: params["capacity"][i - 1]
            for i in model.centers
        },
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.center_capacity = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}
```

#### C-direct.py

```python
import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of length 7
    transport_cost = params["transport_cost"]  # 7x9 matrix
    demand = params["demand"]               # list of length 9
    capacity = params["capacity"]           # list of length 7

    num_centers = 7
    num_stores = 9
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("SupplyChainMasters")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    y = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity if open
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacity[i] * y[i],
            name=f"capacity_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}
```

### 5. Values on the stated and resampled instances

#### param_screen

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 580131.0 (optimal) | 580131.0 (optimal) | 580131.0 (optimal) |
| 1 | 654278.1636256069 (optimal) | 654278.1636256069 (optimal) | 654278.1636256069 (optimal) |
| 2 | 557874.7381816844 (optimal) | 557874.7381816844 (optimal) | 557874.7381816845 (optimal) |
| 3 | 534244.1036702914 (optimal) | 534244.1036702914 (optimal) | 534244.1036702914 (optimal) |
| 4 | 649563.2619204012 (optimal) | 649563.2619204012 (optimal) | 649563.2619204012 (optimal) |
| 5 | 616180.9280864965 (optimal) | 616180.9280864965 (optimal) | 616180.9280864967 (optimal) |

#### independent

Decision: ACCEPT; clique A-direct, B-structured, C-direct; informative instances [0, 1, 2, 3, 4, 5]. Instance 0 is the stated instance.

| Instance | A-direct | B-structured | C-direct |
|---|---|---|---|
| 0 (stated) | 580131.0 (optimal) | 580131.0 (optimal) | 580131.0 (optimal) |
| 1 | 654278.1636256069 (optimal) | 654278.1636256069 (optimal) | 654278.1636256069 (optimal) |
| 2 | 557874.7381816844 (optimal) | 557874.7381816844 (optimal) | 557874.7381816845 (optimal) |
| 3 | 534244.1036702914 (optimal) | 534244.1036702914 (optimal) | 534244.1036702914 (optimal) |
| 4 | 649563.2619204012 (optimal) | 649563.2619204012 (optimal) | 649563.2619204012 (optimal) |
| 5 | 616180.9280864965 (optimal) | 616180.9280864965 (optimal) | 616180.9280864967 (optimal) |

### 6. Data-verification replies

#### Family A (DeepSeek-V4-Flash)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch": [], "not_stated": []}
```

#### Family B (GPT-6.1 Sol)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

```json
{"mismatch":[],"not_stated":[]}
```

#### Family C (Claude Sonnet 5.5)

Status ok; attempts 1; flag_mismatch False; flag_not_stated False; flag_any False.

````json
```json
{
  "mismatch": [],
  "not_stated": []
}
```
````

