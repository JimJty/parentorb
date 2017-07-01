from core.models import Action
from zappa.async import run


# def sample_job(action_id):
#
#     print "processing: %s" % action_id
#
#     #run(process_sub_task, (9,))



def process_action(action_id):

    print "processing: %s" % Action.process_by_id(action_id)