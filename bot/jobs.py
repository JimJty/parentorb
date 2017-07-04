from django.core.exceptions import ObjectDoesNotExist

from core.models import Action, AppUser
from zappa.async import run
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# def sample_job(action_id):
#
#     print "processing: %s" % action_id
#
#     #run(process_sub_task, (9,))



def process_action(action_id):

    print "processing: %s" % Action.process_by_id(action_id)

def schedule_all_users():

    users = AppUser.get_users_to_schedule()
    logger.info("found %s users to schedule" % users.count())

    for u in users:
        run(schedule_user, (u.id,))


def schedule_user(user_id):

    try:
        user = AppUser.objects.get(id=user_id)
    except ObjectDoesNotExist:
        logger.error("user_id not found: %s", user_id)
        return

    logger.info("scheduling: %s", user.id)
    user.schedule_actions()



