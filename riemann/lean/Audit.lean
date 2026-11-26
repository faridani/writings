import Riemann
import Lean.Util.CollectAxioms

/-!
Check all exported theorems in our namespace, including their transitive
dependencies. Reject unfinished proofs and extra computation axioms.
The ordinary foundational axioms used by Lean/Mathlib remain explicit.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := #[`propext, `Quot.sound, `Classical.choice]
  let mut checked := 0
  for (name, info) in env.constants.toList do
    if name.getRoot == `RiemannEssay then
      match info with
      | .axiomInfo _ =>
          throwError "Unexpected local axiom: {name}"
      | .thmInfo _ =>
          let axioms ← collectAxioms name
          let extra := axioms.filter fun axiomName => !allowed.contains axiomName
          unless extra.isEmpty do
            throwError "Theorem {name} uses unapproved axioms: {extra}"
          checked := checked + 1
          logInfo m!"AUDIT {name}: {axioms}"
      | _ => pure ()
  if checked == 0 then
    throwError "No RiemannEssay theorems were found."
  logInfo m!"AUDIT PASSED: {checked} theorem declarations; only standard foundational axioms."
