#!/bin/bash
# Full-Suite Smoke Test — Jeff v5.0 + v6.0
# Beklenen: <2dk, "ALL TESTS PASSED"

SCRIPTS_DIR="$HOME/.hermes/scripts"
PASS=0; TOTAL=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { echo "  ❌ $1 (got: ${2:0:60})"; }

run() {
    TOTAL=$((TOTAL+1))
    local out
    out=$(cd "$SCRIPTS_DIR" && python3 $1 2>/dev/null)
    if echo "$out" | grep -qF "$2"; then pass "$1"; else fail "$1" "$out"; fi
}

echo "🔥 SMOKE TEST — Jeff v5.0 + v6.0"
echo "================================="

run "consciousness_stream.py --hours 2" "🧠"
run "predictive_engine.py patterns" "Toplam olay"  
run "complex_mood_engine.py --list" "hevesli"
run "strategy_planner.py current" "plan"

# v6.0 modules
run "meta_learner.py plan TestAPI" "OGRENME"
run "creativity_engine.py ideas -c 1" "Puan"
run "reverse_thinker.py reverse Test" "risk"
run "autonomous_agent.py execute disk_temizle" "disk_temizle"
run "responsibility_logger.py stats" "Toplam"
run "pragmatics_engine.py analyze test" "ALT METIN"
run "humor_detector.py detect Test" "MIZAH"
run "swarm_orchestrator.py decompose Test" "alt gorev"
run "swarm_communicator.py send a b hello" "Mesaj"
run "swarm_merger.py list" "task"
run "ethics_engine.py check test" "skor"
run "value_based_filter.py evaluate test" "KABUL"

echo "================================="
echo "🔥 $PASS/$TOTAL PASSED"
[ "$PASS" = "$TOTAL" ] && echo "ALL TESTS PASSED" && exit 0 || exit 1
