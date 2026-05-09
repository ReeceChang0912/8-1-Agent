import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'
from family_agent.core import FamilyAgentCore
agent = FamilyAgentCore()
print('members:', len(agent.members))
print('reminders:', len(agent.reminders))
for label, attr in [('shopping', agent.shopping_list.get_items()),
                     ('photos', agent.photo_memory.photos)]:
    try: print(f'{label}: {len(attr)}')
    except Exception as e: print(f'{label}: FAIL {e}')
print('knowledge:', end=' ')
try: print(len(agent.knowledge_base.metadata_index))
except Exception as e: print(f'FAIL {e}')
print('tasks:', end=' ')
try: print(len(agent.task_manager.get_my_tasks('', 'all')))
except Exception as e: print(f'FAIL {e}')
