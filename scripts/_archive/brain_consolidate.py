"""Brain consolidation — learning + health + budget at conversation boundaries."""
import sys
sys.path.insert(0, '/home/hermes/.hermes')
from brain.learning import get_lessons_summary, save_lesson, sync_all_to_mnemosyne
from brain.monitor import check_health
from brain.accounting import get_budget_left, get_daily_usage

health = check_health()
budget = get_budget_left()
daily = get_daily_usage()

save_lesson(
    trigger="conversation_end",
    lesson=f"Consolidation: health={health['status']}, budget=${budget:.2f}",
    category="system",
    source="brain_consolidator"
)

try:
    result = sync_all_to_mnemosyne()
    print(f"synced: {result}")
except Exception as e:
    print(f"sync failed: {e}")

print(f"health={health['status']} budget=${budget:.2f} daily={daily}")
